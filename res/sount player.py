import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QListWidgetItem, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class SoundItemWidget(QWidget):
    def __init__(self, file_path, parent_list_widget):
        super().__init__()
        self.file_path = file_path
        self.parent_list_widget = parent_list_widget
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        self.label = QLabel(file_path.stem)
        layout.addWidget(self.label, stretch=1)
        
        # Play Button
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.play_sound)
        layout.addWidget(self.btn_play)
        
        # Copy Name Button
        self.btn_copy = QPushButton("Copy Name")
        self.btn_copy.clicked.connect(self.copy_name)
        layout.addWidget(self.btn_copy)
        
        # Rename Button
        self.btn_rename = QPushButton("Rename")
        self.btn_rename.clicked.connect(self.rename_file)
        layout.addWidget(self.btn_rename)
        
        # Delete Button
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_file)
        layout.addWidget(self.btn_delete)

        # Audio Player
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setSource(QUrl.fromLocalFile(str(self.file_path)))
        self.audio.setVolume(0.7)

    def play_sound(self):
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
                self.label.setText(new_name)
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

class SoundboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundboard")
        self.setMinimumSize(800, 600)
        
        self.list_widget = QListWidget()
        self.setCentralWidget(self.list_widget)
    
        sounds_dir = Path(__file__).parent / "sounds"
        sounds_dir.mkdir(exist_ok=True)
        sound_files = [f for f in sounds_dir.iterdir() if f.suffix in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']]
        
        for f in sorted(sound_files):
            item = QListWidgetItem(self.list_widget)
            item_widget = SoundItemWidget(f, self.list_widget)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(item, item_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SoundboardApp()
    window.show()
    sys.exit(app.exec())