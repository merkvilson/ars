import sys
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QSlider, QLabel)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from pydub import AudioSegment
import tempfile

class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(500)
        self.audio_data = None
        self.trim_start = 0
        self.trim_end = 0
        self.zoom_level = 1.0  # 1.0 = normal, >1 = zoomed in
        self.pan_offset = 0  # Horizontal pan position when zoomed
        self.fade_in_samples = 0
        self.fade_out_samples = 0
        
    def set_audio(self, data, trim_start, trim_end, fade_in_samples=0, fade_out_samples=0):
        self.audio_data = data
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.fade_in_samples = fade_in_samples
        self.fade_out_samples = fade_out_samples
        self.update()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if self.audio_data is None:
            return
        
        # Get mouse position relative to widget
        mouse_x = event.position().x()
        widget_width = self.width()
        
        # Calculate zoom change
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        # Calculate new zoom level
        old_zoom = self.zoom_level
        self.zoom_level = max(1.0, min(100.0, self.zoom_level * zoom_factor))
        
        # If zooming in, adjust pan to keep the mouse position stable
        if self.zoom_level > 1.0:
            # Calculate the position in the data that the mouse is pointing to
            mouse_data_pos = (mouse_x + self.pan_offset) / old_zoom
            
            # Calculate new pan offset to keep the same data point under the mouse
            new_pan = mouse_data_pos * self.zoom_level - mouse_x
            
            # Clamp pan offset to valid range
            max_pan = widget_width * (self.zoom_level - 1)
            self.pan_offset = max(0, min(max_pan, new_pan))
        else:
            # Reset pan when fully zoomed out
            self.pan_offset = 0
        
        self.update()
    
    def mousePressEvent(self, event):
        """Start panning when zoomed in"""
        if event.button() == Qt.MouseButton.LeftButton and self.zoom_level > 1.0:
            self.last_mouse_x = event.position().x()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """Handle panning when dragging"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.zoom_level > 1.0:
            dx = event.position().x() - self.last_mouse_x
            self.last_mouse_x = event.position().x()
            
            # Update pan offset
            max_pan = self.width() * (self.zoom_level - 1)
            self.pan_offset = max(0, min(max_pan, self.pan_offset - dx))
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Stop panning"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
    def paintEvent(self, event):
        if self.audio_data is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        mid = h // 2
        
        # Fill background
        painter.fillRect(0, 0, w, h, QColor('#1a1a1a'))
        
        # Get audio data (convert to mono if stereo)
        data = self.audio_data
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        
        # Normalize
        if data.max() > 0:
            data = data / data.max()
        
        # Calculate visible range based on zoom and pan
        visible_width = w * self.zoom_level
        visible_start = self.pan_offset
        visible_end = visible_start + w
        
        # Calculate trim positions in screen space
        trim_start_x = int((self.trim_start / len(self.audio_data)) * visible_width - visible_start)
        trim_end_x = int((self.trim_end / len(self.audio_data)) * visible_width - visible_start)
        
        # Draw waveform with zoom
        samples_per_pixel = len(data) / visible_width
        
        # Calculate fade regions in sample space
        fade_in_end = self.trim_start + self.fade_in_samples
        fade_out_start = self.trim_end - self.fade_out_samples
        
        for x in range(w):
            # Calculate the position in the zoomed waveform
            zoomed_x = visible_start + x
            
            # Calculate corresponding sample index
            sample_idx = int(zoomed_x * samples_per_pixel)
            
            if 0 <= sample_idx < len(data):
                # Get the sample value
                sample_value = data[sample_idx]
                
                # Apply fade effect to the sample value for visualization
                fade_multiplier = 1.0
                if self.trim_start <= sample_idx < fade_in_end and self.fade_in_samples > 0:
                    # Fade in region
                    fade_progress = (sample_idx - self.trim_start) / self.fade_in_samples
                    fade_multiplier = fade_progress
                elif fade_out_start <= sample_idx < self.trim_end and self.fade_out_samples > 0:
                    # Fade out region
                    fade_progress = (self.trim_end - sample_idx) / self.fade_out_samples
                    fade_multiplier = fade_progress
                
                # Apply fade to the visual sample
                faded_sample = sample_value * fade_multiplier
                
                # Determine color based on trim regions
                if x < trim_start_x or x >= trim_end_x:
                    painter.setPen(QPen(QColor('#ff4444'), 1))  # Red for trimmed
                elif self.trim_start <= sample_idx < fade_in_end and self.fade_in_samples > 0:
                    painter.setPen(QPen(QColor('#44aaff'), 1))  # Blue for fade in
                elif fade_out_start <= sample_idx < self.trim_end and self.fade_out_samples > 0:
                    painter.setPen(QPen(QColor('#ffaa44'), 1))  # Orange for fade out
                else:
                    painter.setPen(QPen(QColor('#44ff44'), 1))  # Green for kept
                
                # Draw the waveform line with fade applied
                y = int(mid - faded_sample * (h * 0.4))
                painter.drawLine(x, mid, x, y)
        
        # Draw center line
        painter.setPen(QPen(QColor('#3a3a3a'), 1))
        painter.drawLine(0, mid, w, mid)
        
        # Draw zoom indicator
        if self.zoom_level > 1.0:
            painter.setPen(QPen(QColor('#888888'), 1))
            zoom_text = f"Zoom: {self.zoom_level:.1f}x"
            painter.drawText(10, 20, zoom_text)
            
            # Draw scroll hint
            if self.zoom_level > 1.0:
                hint_text = "Drag to pan"
                painter.drawText(10, 40, hint_text)

class AudioModifier(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Trimmer")
        self.setMinimumSize(900, 650)

        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)
        
        # Sliders
        slider_layout = QVBoxLayout()
        slider_layout.setSpacing(10)
        
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(1000)
        self.start_slider.setValue(0)
        self.start_slider.valueChanged.connect(self.update_trim)
        slider_layout.addWidget(self.start_slider)
        
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(1000)
        self.end_slider.setValue(1000)
        self.end_slider.valueChanged.connect(self.update_trim)
        slider_layout.addWidget(self.end_slider)
        
        # Fade sliders (side by side)
        fade_layout = QHBoxLayout()
        fade_layout.setSpacing(20)
        
        # Fade In
        fade_in_container = QVBoxLayout()
        fade_in_container.addWidget(QLabel("Fade In:"))
        self.fade_in_slider = QSlider(Qt.Orientation.Horizontal)
        self.fade_in_slider.setMinimum(0)
        self.fade_in_slider.setMaximum(500)  # Max 50% of audio
        self.fade_in_slider.setValue(0)
        self.fade_in_slider.valueChanged.connect(self.update_trim)
        fade_in_container.addWidget(self.fade_in_slider)
        fade_layout.addLayout(fade_in_container)
        
        # Fade Out
        fade_out_container = QVBoxLayout()
        fade_out_container.addWidget(QLabel("Fade Out:"))
        self.fade_out_slider = QSlider(Qt.Orientation.Horizontal)
        self.fade_out_slider.setMinimum(0)
        self.fade_out_slider.setMaximum(500)  # Max 50% of audio
        self.fade_out_slider.setValue(500)  # Start at right (no fade)
        self.fade_out_slider.setInvertedAppearance(True)  # Reverse the slider
        self.fade_out_slider.valueChanged.connect(self.update_trim)
        fade_out_container.addWidget(self.fade_out_slider)
        fade_layout.addLayout(fade_out_container)
        
        slider_layout.addLayout(fade_layout)
        
        layout.addLayout(slider_layout)
        
        # Playback buttons
        play_layout = QHBoxLayout()
        
        self.play_original_btn = QPushButton("▶ Play Original")
        self.play_original_btn.clicked.connect(self.play_original)
        self.play_original_btn.setEnabled(False)
        play_layout.addWidget(self.play_original_btn)
        
        self.play_trimmed_btn = QPushButton("▶ Play Trimmed")
        self.play_trimmed_btn.clicked.connect(self.play_trimmed)
        self.play_trimmed_btn.setEnabled(False)
        play_layout.addWidget(self.play_trimmed_btn)
        
        layout.addLayout(play_layout)
        
        # Load and save buttons
        action_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load Audio File")
        load_btn.clicked.connect(self.load_audio)
        action_layout.addWidget(load_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_audio)
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.save_btn)
        
        self.save_as_btn = QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.trim_and_save)
        self.save_as_btn.setEnabled(False)
        action_layout.addWidget(self.save_as_btn)
    
        
        layout.addLayout(action_layout)
        
        self.audio_data = None
        self.sample_rate = None
        self.file_path = None
        self.audio_segment = None
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.temp_files = []

        
    def load_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a)")
        
        if not file_path:
            return
        
        self.file_path = Path(file_path)
        
        try:
            self.audio_segment = AudioSegment.from_file(file_path)
            self.sample_rate = self.audio_segment.frame_rate
            samples = np.array(self.audio_segment.get_array_of_samples())
            
            if self.audio_segment.channels == 2:
                samples = samples.reshape((-1, 2))
            
            self.audio_data = samples
            
            # Reset zoom when loading new file
            self.waveform.zoom_level = 1.0
            self.waveform.pan_offset = 0
            
            # Auto-detect silence
            if len(self.audio_data.shape) > 1:
                mono = self.audio_data.mean(axis=1)
            else:
                mono = self.audio_data
            
            threshold = np.max(np.abs(mono)) * 0.01
            
            trim_start = 0
            for i in range(len(mono)):
                if np.abs(mono[i]) > threshold:
                    trim_start = i
                    break
            
            trim_end = len(mono)
            for i in range(len(mono) - 1, -1, -1):
                if np.abs(mono[i]) > threshold:
                    trim_end = i
                    break
            
            # Set sliders
            self.start_slider.setValue(int(trim_start / len(mono) * 1000))
            self.end_slider.setValue(int(trim_end / len(mono) * 1000))
            
            # Reset fade sliders
            self.fade_in_slider.setValue(0)
            self.fade_out_slider.setValue(0)
            
            self.update_trim()
            self.play_original_btn.setEnabled(True)
            self.play_trimmed_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.save_as_btn.setEnabled(True)
            
        except Exception as e:
            pass
    
    def update_trim(self):
        if self.audio_data is None:
            return
        
        total_samples = len(self.audio_data)
        self.trim_start = int((self.start_slider.value() / 1000) * total_samples)
        self.trim_end = int((self.end_slider.value() / 1000) * total_samples)
        
        # Ensure start < end
        if self.trim_start >= self.trim_end:
            self.trim_start = max(0, self.trim_end - 1000)
        
        # Calculate fade samples
        trimmed_length = self.trim_end - self.trim_start
        self.fade_in_samples = int((self.fade_in_slider.value() / 1000) * trimmed_length)
        self.fade_out_samples = int((self.fade_out_slider.value() / 1000) * trimmed_length)
        
        self.waveform.set_audio(self.audio_data, self.trim_start, self.trim_end, 
                                self.fade_in_samples, self.fade_out_samples)
    
    def play_original(self):
        if self.audio_segment is None:
            return
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        self.audio_segment.export(temp_file.name, format='wav')
        self.temp_files.append(temp_file.name)
        
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(temp_file.name))
        self.player.play()
    
    def play_trimmed(self):
        if self.audio_segment is None:
            return
        
        start_ms = int((self.trim_start / self.sample_rate) * 1000)
        end_ms = int((self.trim_end / self.sample_rate) * 1000)
        
        trimmed_segment = self.audio_segment[start_ms:end_ms]
        
        # Apply fade effects
        fade_in_ms = int((self.fade_in_samples / self.sample_rate) * 1000)
        fade_out_ms = int((self.fade_out_samples / self.sample_rate) * 1000)
        
        if fade_in_ms > 0:
            trimmed_segment = trimmed_segment.fade_in(fade_in_ms)
        if fade_out_ms > 0:
            trimmed_segment = trimmed_segment.fade_out(fade_out_ms)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        trimmed_segment.export(temp_file.name, format='wav')
        self.temp_files.append(temp_file.name)
        
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(temp_file.name))
        self.player.play()
    
    def get_processed_audio(self):
        """Get the trimmed and faded audio segment"""
        if self.audio_segment is None:
            return None
        
        start_ms = int((self.trim_start / self.sample_rate) * 1000)
        end_ms = int((self.trim_end / self.sample_rate) * 1000)
        
        trimmed_segment = self.audio_segment[start_ms:end_ms]
        
        # Apply fade effects
        fade_in_ms = int((self.fade_in_samples / self.sample_rate) * 1000)
        fade_out_ms = int((self.fade_out_samples / self.sample_rate) * 1000)
        
        if fade_in_ms > 0:
            trimmed_segment = trimmed_segment.fade_in(fade_in_ms)
        if fade_out_ms > 0:
            trimmed_segment = trimmed_segment.fade_out(fade_out_ms)
        
        return trimmed_segment
    
    def save_audio(self):
        """Save with the same filename (overwriting original)"""
        if self.audio_segment is None or self.file_path is None:
            return
        
        trimmed_segment = self.get_processed_audio()
        if trimmed_segment:
            trimmed_segment.export(str(self.file_path), format=self.file_path.suffix[1:])
    
    def trim_and_save(self):
        if self.audio_segment is None:
            return
        
        trimmed_segment = self.get_processed_audio()
        if not trimmed_segment:
            return
        
        original_ext = self.file_path.suffix.lower()
        filter_str = f"{original_ext.upper()[1:]} Files (*{original_ext});;WAV Files (*.wav);;All Files (*.*)"
        default_name = str(self.file_path.parent / f"{self.file_path.stem}_trimmed{original_ext}")
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Trimmed Audio", default_name, filter_str)
        
        if save_path:
            trimmed_segment.export(save_path, format=Path(save_path).suffix[1:])
    
    def closeEvent(self, event):
        # Clean up temp files
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink()
            except:
                pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioModifier()
    window.show()
    sys.exit(app.exec())