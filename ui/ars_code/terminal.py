import sys
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont, QColor, QTextCharFormat

import sys
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont, QColor, QTextCharFormat

class OutputStream(QObject):
    text_written = pyqtSignal(str)
    
    def __init__(self, original_stream):
        super().__init__()
        self.original_stream = original_stream

    def write(self, text):
        # Write to original stream so it still appears in the real console/terminal
        if self.original_stream:
            self.original_stream.write(text)
        # Emit signal to update GUI
        self.text_written.emit(text)

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()
            
    def isatty(self):
        if self.original_stream:
            return getattr(self.original_stream, 'isatty', lambda: False)()
        return False

# Global instances to manage redirection centrally
_stdout_redirector = None
_stderr_redirector = None

def install_redirectors():
    """
    Installs the global stream redirectors if they haven't been installed yet.
    This ensures that sys.stdout and sys.stderr are replaced only once,
    and multiple TerminalWidgets can subscribe to the same signals.
    """
    global _stdout_redirector, _stderr_redirector
    
    if _stdout_redirector is None:
        _stdout_redirector = OutputStream(sys.stdout)
        sys.stdout = _stdout_redirector
    
    if _stderr_redirector is None:
        _stderr_redirector = OutputStream(sys.stderr)
        sys.stderr = _stderr_redirector

class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        # Dark theme style
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e; 
                color: #d4d4d4; 
                font-family: Consolas, 'Courier New', monospace;
                border: none;
            }
        """)
        
        # Set font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        
        # Limit the number of lines to prevent memory issues
        self.text_edit.setMaximumBlockCount(5000)

        self.layout.addWidget(self.text_edit)
        
        # Ensure redirectors are installed
        install_redirectors()
        
        # Connect to the global redirectors
        if _stdout_redirector:
            _stdout_redirector.text_written.connect(self.on_stdout)
        if _stderr_redirector:
            _stderr_redirector.text_written.connect(self.on_stderr)

    def on_stdout(self, text):
        self.append_text(text, "#cccccc") # Light gray for stdout

    def on_stderr(self, text):
        self.append_text(text, "#ff6b6b") # Red-ish for stderr

    def log(self, message, color="white"):
        """
        Log a message directly to the terminal.
        """
        self.append_text(message, color)

    def append_text(self, text, color_name):
        # Move cursor to end
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Set format
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_name))
        cursor.setCharFormat(fmt)
        
        cursor.insertText(text)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def clear_terminal(self):
        self.text_edit.clear()

    def closeEvent(self, event):
        # Disconnect signals when widget is closed to prevent trying to write to a deleted widget
        if _stdout_redirector:
            try:
                _stdout_redirector.text_written.disconnect(self.on_stdout)
            except TypeError: pass # Might not be connected
            
        if _stderr_redirector:
            try:
                _stderr_redirector.text_written.disconnect(self.on_stderr)
            except TypeError: pass

        super().closeEvent(event)
