import sys
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QApplication
from PyQt6.QtCore import Qt

# Handle imports whether run as script or module
try:
    from .editor import CodeEditor
    from .terminal import TerminalWidget
except ImportError:
    try:
        from editor import CodeEditor
        from terminal import TerminalWidget
    except ImportError:
        sys.path.append(str(Path(__file__).parent))
        from editor import CodeEditor
        from terminal import TerminalWidget


class CodeEditorWidget(QWidget):
    """Combined Code Editor and Terminal widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for resizable areas
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)
        
        # Create Editor
        self.code_editor = CodeEditor()
        self.splitter.addWidget(self.code_editor)
        
        # Create Terminal
        self.terminal = TerminalWidget()
        self.splitter.addWidget(self.terminal)
        
        # Set initial sizes (80% editor, 20% terminal)
        self.splitter.setSizes([800, 200])
    
    def set_code(self, text):
        """Set the code editor content."""
        self.code_editor.setPlainText(text)
    
    def get_code(self):
        """Get the code editor content."""
        return self.code_editor.toPlainText()
    
    def run_code(self, namespace_injection=None):
        """Run the code in the editor."""
        self.code_editor.run_code(namespace_injection)
    
    def save_script(self):
        """Save the current script."""
        self.code_editor.save_script()
    
    def set_font_size(self, size):
        """Set editor font size."""
        self.code_editor.set_font_size(size)
    
    def set_alpha(self, alpha):
        """Set editor transparency."""
        self.code_editor.set_alpha(alpha)
    
    def clear_terminal(self):
        """Clear the terminal output."""
        self.terminal.clear_terminal()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CodeEditorWidget()
    window.setWindowTitle("Code Editor")
    window.resize(1200, 800)
    window.set_code("# Test script\nprint('Hello, World!')")
    window.show()
    sys.exit(app.exec())
