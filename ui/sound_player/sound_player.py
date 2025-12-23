import sys
import os
from pathlib import Path

# Suppress Qt debug/info messages from FFmpeg and other Qt subsystems
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false;qt.multimedia.ffmpeg=false"

# Add project root to sys.path to allow imports from ui, core, etc.
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QListWidgetItem, QInputDialog, QMessageBox,
                             QGraphicsView, QGraphicsScene)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from ui.widgets.b_button import BButton, BButtonConfig
from theme.fonts import font_icons as ic

class BButtonWidget(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("border: none; background: transparent;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        
        self.button = BButton(config)
        self.scene.addItem(self.button)
        
        # Initial size adjustment
        self.adjust_size()
        
    def adjust_size(self):
        # Calculate bounding rect including children (additional text)
        rect = self.button.childrenBoundingRect() | self.button.boundingRect()
        
        # Add padding for hover effects/ripples
        margin = 0 
        width = rect.width() + margin
        height = rect.height() + margin
        
        self.setFixedSize(int(width), int(height))
        # Center the scene on the button (button is at 0,0 usually, but children might extend it)
        # BButton is centered at 0,0.
        # childrenBoundingRect might be offset.
        
        self.view.setSceneRect(rect.x() - margin/2, rect.y() - margin/2, width, height)

    def update_text(self, text):
        self.button.additional_text = text
        self.button._update_additional_text()
        self.adjust_size()

class SimpleButton(QPushButton):
    def __init__(self, text, icon_char=None, callback=None, parent=None):
        super().__init__(text, parent)
        self.callback = callback
        if icon_char:
            self.setText(f"{icon_char} {text}" if text else icon_char)
            # Assuming icon_char is from a font like FontAwesome or similar
            # You might need to set the font here if it's a special icon font
            # self.setFont(QFont("YourIconFont", 12)) 
        
        # Basic styling to match the dark theme roughly
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ddd;
                border: none;
                padding: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        if callback:
            self.clicked.connect(callback)

class SoundItemWidget(QWidget):
    item_clicked = pyqtSignal(Path)
    play_requested = pyqtSignal(Path)
    rename_requested = pyqtSignal(Path, str) # old_path, new_name
    delete_requested = pyqtSignal(Path)

    def __init__(self, file_path, parent_list_widget):
        super().__init__()
        self.file_path = file_path
        self.parent_list_widget = parent_list_widget
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)
        
        # Play/Name Button
        # Using standard QPushButton instead of heavy BButtonWidget
        self.btn_play = SimpleButton(file_path.stem, ic.ICON_PLAYER_PLAY, self.request_play)
        # Set font for icon if needed, assuming 'ic' provides characters for a specific font
        from theme.fonts.new_fonts import get_font
        self.btn_play.setFont(get_font(14))
        layout.addWidget(self.btn_play, stretch=1)
        
        # Copy Name Button
        self.btn_copy = SimpleButton("", ic.ICON_CLIPBOARD_PASTE, self.copy_name)
        self.btn_copy.setFont(get_font(14))
        self.btn_copy.setToolTip("Copy Name")
        self.btn_copy.setFixedWidth(30)
        layout.addWidget(self.btn_copy)
        
        # Rename Button
        self.btn_rename = SimpleButton("", ic.ICON_TEXT_INPUT, self.rename_file)
        self.btn_rename.setFont(get_font(14))
        self.btn_rename.setToolTip("Rename")
        self.btn_rename.setFixedWidth(30)
        layout.addWidget(self.btn_rename)
        
        # Delete Button
        self.btn_delete = SimpleButton("", ic.ICON_TRASH, self.delete_file)
        self.btn_delete.setFont(get_font(14))
        self.btn_delete.setToolTip("Delete")
        self.btn_delete.setFixedWidth(30)
        layout.addWidget(self.btn_delete)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.item_clicked.emit(self.file_path)
            # Also select the item in the list widget visually
            for i in range(self.parent_list_widget.count()):
                item = self.parent_list_widget.item(i)
                if self.parent_list_widget.itemWidget(item) == self:
                    self.parent_list_widget.setCurrentItem(item)
                    break
        super().mousePressEvent(event)

    def request_play(self):
        self.play_requested.emit(self.file_path)

    def copy_name(self):
        QApplication.clipboard().setText(self.file_path.stem)

    def rename_file(self):
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=self.file_path.stem)
        if ok and new_name:
            self.rename_requested.emit(self.file_path, new_name)

    def update_path(self, new_path):
        self.file_path = new_path
        self.btn_play.setText(f"{ic.ICON_PLAYER_PLAY} {new_path.stem}")

    def delete_file(self):
        reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {self.file_path.name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.file_path)

class SoundboardWidget(QWidget):
    sound_selected = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.list_widget.itemClicked.connect(self.on_item_clicked)
    
        # Shared Media Player
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.7)

        # Defer loading to prevent UI freeze
        QTimer.singleShot(10, self.populate_list)

    def populate_list(self):
        # Point to res/sounds from ui/sound_player/sound_player.py
        # Path(__file__).parents[2] is the project root (ARS)
        sounds_dir = Path(__file__).parents[2] / "res" / "sounds"
        sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Use a generator or chunking to avoid blocking
        self.sound_files = sorted([f for f in sounds_dir.iterdir() if f.suffix in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']])
        self.load_index = 0
        self.chunk_size = 10
        
        self.load_timer = QTimer(self)
        self.load_timer.timeout.connect(self.load_chunk)
        self.load_timer.start(20) # Increased from 0 to 20ms to allow UI updates

    def load_chunk(self):
        if self.load_index >= len(self.sound_files):
            self.load_timer.stop()
            return

        end_index = min(self.load_index + self.chunk_size, len(self.sound_files))
        # Temporarily disable updates to prevent layout thrashing
        self.list_widget.setUpdatesEnabled(False)
        try:
            for i in range(self.load_index, end_index):
                f = self.sound_files[i]
                item = QListWidgetItem(self.list_widget)
                item_widget = SoundItemWidget(f, self.list_widget)
                
                # Connect signals
                item_widget.item_clicked.connect(self.sound_selected.emit)
                item_widget.play_requested.connect(self.play_sound)
                item_widget.rename_requested.connect(self.rename_file)
                item_widget.delete_requested.connect(self.delete_file)
                
                item.setSizeHint(item_widget.sizeHint())
                self.list_widget.setItemWidget(item, item_widget)
        finally:
            self.list_widget.setUpdatesEnabled(True)
        
        self.load_index = end_index

    def play_sound(self, file_path):
        self.sound_selected.emit(file_path)
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(str(file_path)))
        self.player.play()

    def rename_file(self, old_path, new_name):
        new_path = old_path.with_name(new_name + old_path.suffix)
        try:
            self.player.setSource(QUrl()) # Release file lock
            old_path.rename(new_path)
            
            # Update widget
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                widget = self.list_widget.itemWidget(item)
                if widget and widget.file_path == old_path:
                    widget.update_path(new_path)
                    break
                    
            # Restore player if needed (optional, maybe don't auto-play after rename)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not rename file: {e}")

    def delete_file(self, file_path):
        try:
            self.player.setSource(QUrl()) # Release file lock
            file_path.unlink()
            # Remove from list
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                widget = self.list_widget.itemWidget(item)
                if widget and widget.file_path == file_path:
                    self.list_widget.takeItem(i)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not delete file: {e}")

    def on_item_clicked(self, item):
        widget = self.list_widget.itemWidget(item)
        if widget:
            self.sound_selected.emit(widget.file_path)

class SoundboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundboard")
        self.setMinimumSize(800, 600)
        self.setCentralWidget(SoundboardWidget())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SoundboardApp()
    window.show()
    sys.exit(app.exec())