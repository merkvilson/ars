import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class SoundboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soundboard")
        self.setMinimumSize(600, 400)
        # self.setStyleSheet("""
        #     QMainWindow { background-color: #1a1a1a; }
        #      QPushButton {
        #          background-color: #2a2a2a; color: #e0e0e0; border: 2px solid #3a3a3a;
        #          border-radius: 8px; font-size: 14px; padding: 10px; min-height: 50px;
        #     }
        #     QPushButton:hover { background-color: #3a3a3a; border: 2px solid #4a4a4a; }
        #     QPushButton:pressed { background-color: #4a4a4a; }
        # """)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        grid = QGridLayout(widget)
    
        sounds_dir = Path(__file__).parent / "sounds"
        sounds_dir.mkdir(exist_ok=True)
        sound_files = [f for f in sounds_dir.iterdir() if f.suffix in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']]
        
        self.players = {}
        for i, f in enumerate(sorted(sound_files)):
            player = QMediaPlayer()
            audio = QAudioOutput()
            player.setAudioOutput(audio)
            player.setSource(QUrl.fromLocalFile(str(f)))
            audio.setVolume(0.7)
            self.players[f] = (player, audio)
            
            btn = QPushButton(f.stem)
            btn.clicked.connect(lambda checked, p=player: (p.stop(), p.setPosition(0), p.play()))
            grid.addWidget(btn, i // 3, i % 3)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SoundboardApp()
    window.show()
    sys.exit(app.exec())