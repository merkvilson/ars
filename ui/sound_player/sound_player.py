import sys
from pathlib import Path

# Add project root to sys.path to allow imports from ui, core, etc.
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QListWidgetItem, QInputDialog, QMessageBox,
                             QGraphicsView, QGraphicsScene)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
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

class SoundItemWidget(QWidget):
    item_clicked = pyqtSignal(Path)

    def __init__(self, file_path, parent_list_widget):
        super().__init__()
        self.file_path = file_path
        self.parent_list_widget = parent_list_widget
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Play/Name Button
        play_config = BButtonConfig(
            symbol=ic.ICON_PLAYER_PLAY,
            additional_text=file_path.stem,
            use_extended_shape=True,
            callbackL=self.play_sound,
        )
        self.btn_play = BButtonWidget(play_config)
        layout.addWidget(self.btn_play)
        
        layout.addStretch(1)
        
        # Copy Name Button
        copy_config = BButtonConfig(
            symbol=ic.ICON_CLIPBOARD_PASTE,
            callbackL=self.copy_name,
        )
        self.btn_copy = BButtonWidget(copy_config)
        layout.addWidget(self.btn_copy)
        
        # Rename Button
        rename_config = BButtonConfig(
            symbol=ic.ICON_TEXT_INPUT,
            callbackL=self.rename_file,
        )
        self.btn_rename = BButtonWidget(rename_config)
        layout.addWidget(self.btn_rename)
        
        # Delete Button
        delete_config = BButtonConfig(
            symbol=ic.ICON_TRASH,
            callbackL=self.delete_file,
        )
        self.btn_delete = BButtonWidget(delete_config)
        layout.addWidget(self.btn_delete)

        # Audio Player
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setSource(QUrl.fromLocalFile(str(self.file_path)))
        self.audio.setVolume(0.7)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"DEBUG: SoundItemWidget clicked: {self.file_path}")
            self.item_clicked.emit(self.file_path)
            # Also select the item in the list widget visually
            for i in range(self.parent_list_widget.count()):
                item = self.parent_list_widget.item(i)
                if self.parent_list_widget.itemWidget(item) == self:
                    self.parent_list_widget.setCurrentItem(item)
                    break
        super().mousePressEvent(event)

    def play_sound(self):
        print(f"DEBUG: Play button clicked: {self.file_path}")
        self.item_clicked.emit(self.file_path) # Also select when playing
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()
        self.player.setPosition(0)
        self.player.play()

    def copy_name(self):
        QApplication.clipboard().setText(self.file_path.stem)

    def rename_file(self):
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=self.file_path.stem)
        if ok and new_name:
            new_path = self.file_path.with_name(new_name + self.file_path.suffix)
            try:
                self.player.setSource(QUrl()) # Release file lock
                self.file_path.rename(new_path)
                self.file_path = new_path
                self.btn_play.update_text(new_name)
                self.player.setSource(QUrl.fromLocalFile(str(self.file_path)))
            except Exception as e:
                self.player.setSource(QUrl.fromLocalFile(str(self.file_path))) # Restore on error
                QMessageBox.critical(self, "Error", f"Could not rename file: {e}")

    def delete_file(self):
        reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {self.file_path.name}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.player.setSource(QUrl()) # Release file lock
                self.file_path.unlink()
                # Remove from list
                for i in range(self.parent_list_widget.count()):
                    item = self.parent_list_widget.item(i)
                    if self.parent_list_widget.itemWidget(item) == self:
                        self.parent_list_widget.takeItem(i)
                        break
            except Exception as e:
                self.player.setSource(QUrl.fromLocalFile(str(self.file_path))) # Restore on error
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")

class SoundboardWidget(QWidget):
    sound_selected = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.list_widget.itemClicked.connect(self.on_item_clicked)
    
        # Point to res/sounds from ui/sound_player/sound_player.py
        # Path(__file__).parents[2] is the project root (ARS)
        sounds_dir = Path(__file__).parents[2] / "res" / "sounds"
        sounds_dir.mkdir(parents=True, exist_ok=True)
        sound_files = [f for f in sounds_dir.iterdir() if f.suffix in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']]
        
        for f in sorted(sound_files):
            item = QListWidgetItem(self.list_widget)
            item_widget = SoundItemWidget(f, self.list_widget)
            item_widget.item_clicked.connect(self.sound_selected.emit)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(item, item_widget)

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