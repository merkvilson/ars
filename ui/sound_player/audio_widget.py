import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt

# Add project root to sys.path to allow imports from ui, core, etc.
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Handle imports whether run as script or module
try:
    from .sound_player import SoundboardWidget
    from .sound_modifier import AudioModifierWidget
except ImportError:
    try:
        from sound_player import SoundboardWidget
        from sound_modifier import AudioModifierWidget
    except ImportError:
        # Add current directory to path if needed
        sys.path.append(str(Path(__file__).parent))
        from sound_player import SoundboardWidget
        from sound_modifier import AudioModifierWidget

class AudioStudio(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Studio")
        self.resize(1200, 800)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Use a splitter for resizable areas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left: Sound Player
        self.sound_player = SoundboardWidget()
        splitter.addWidget(self.sound_player)
        
        # Right: Sound Modifier
        self.sound_modifier = AudioModifierWidget()
        splitter.addWidget(self.sound_modifier)
        
        # Set initial sizes (e.g., 30% left, 70% right)
        splitter.setSizes([300, 900])
        
        # Connect signal
        self.sound_player.sound_selected.connect(self.on_sound_selected)
        
    def on_sound_selected(self, file_path):
        self.sound_modifier.load_from_path(file_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioStudio()
    window.show()
    sys.exit(app.exec())
