import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QTextEdit, QWidget, QHBoxLayout
)
from PyQt6.QtCore import (
    Qt, QRect, QSize, QRegularExpression
)
from PyQt6.QtGui import (
    QColor, QPainter, QFont, QSyntaxHighlighter, QTextCharFormat, QTextFormat, QFontMetrics
)

class PythonHighlighter(QSyntaxHighlighter):
    """
    A syntax highlighter for Python code.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#CF8E6D"))  # Rust/Orange
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "\\bdef\\b", "\\bclass\\b", "\\bif\\b", "\\belif\\b", "\\belse\\b",
            "\\bwhile\\b", "\\bfor\\b", "\\btry\\b", "\\bexcept\\b", "\\bfinally\\b",
            "\\bimport\\b", "\\bfrom\\b", "\\breturn\\b", "\\bpass\\b", "\\bcontinue\\b",
            "\\bbreak\\b", "\\bin\\b", "\\bis\\b", "\\bnot\\b", "\\band\\b", "\\bor\\b",
            "\\byield\\b", "\\bwith\\b", "\\bas\\b", "\\bassert\\b", "\\bdel\\b",
            "\\bglobal\\b", "\\blambda\\b", "\\bnonlocal\\b", "\\braise\\b"
        ]
        self.highlighting_rules.extend(
            (QRegularExpression(pattern), keyword_format) for pattern in keywords
        )

        # Built-in constants format (True, False, None)
        constant_format = QTextCharFormat()
        constant_format.setForeground(QColor("#6D9ECF"))  # Blue
        constant_format.setFontWeight(QFont.Weight.Bold)
        constants = ["\\bTrue\\b", "\\bFalse\\b", "\\bNone\\b"]
        self.highlighting_rules.extend(
            (QRegularExpression(pattern), constant_format) for pattern in constants
        )
        
        # 'self' format
        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#9B70C8")) # Purple
        self_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression("\\bself\\b"), self_format))

        # Function and class name format
        function_class_format = QTextCharFormat()
        function_class_format.setForeground(QColor("#6DAFCF"))  # Light Blue
        function_class_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression("\\bdef\\s+([A-Za-z_][A-Za-z0-9_]*)"), function_class_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression("\\bclass\\s+([A-Za-z_][A-Za-z0-9_]*)"), function_class_format)
        )

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression("#[^\n]*"), comment_format)
        )

        # String format (double-quoted)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#B5CEA8"))  # Light Green/String color
        self.highlighting_rules.append(
            (QRegularExpression("\".*\""), string_format)
        )
        
        # String format (single-quoted)
        self.highlighting_rules.append(
            (QRegularExpression("'.*'"), string_format)
        )

        # Multi-line string formats (triple quotes)
        self.tri_double_quote_format = QTextCharFormat()
        self.tri_double_quote_format.setForeground(QColor("#B5CEA8"))
        self.tri_single_quote_format = QTextCharFormat()
        self.tri_single_quote_format.setForeground(QColor("#B5CEA8"))

        self.tri_double_start = QRegularExpression('"""')
        self.tri_double_end = QRegularExpression('"""')
        self.tri_single_start = QRegularExpression("'''")
        self.tri_single_end = QRegularExpression("'''")

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given text block.
        """
        # Apply standard rules
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                # Handle function/class names (group 1)
                if match.lastCapturedIndex() > 0:
                     self.setFormat(match.capturedStart(1), match.capturedLength(1), format)
                else:
                    self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.setCurrentBlockState(0)

        # Handle multi-line triple double quotes """
        self.highlight_multiline(text, 
                                 self.tri_double_start, 
                                 self.tri_double_end, 
                                 1, 
                                 self.tri_double_quote_format)

        # Handle multi-line triple single quotes '''
        self.highlight_multiline(text, 
                                 self.tri_single_start, 
                                 self.tri_single_end, 
                                 2, 
                                 self.tri_single_quote_format)


    def highlight_multiline(self, text, start_regex, end_regex, state, format):
        """
        Helper function to highlight multi-line blocks (like triple-quoted strings).
        """
        start_index = 0
        
        # Check previous block state
        if self.previousBlockState() == state:
            start_index = 0
        else:
            match = start_regex.match(text)
            if match.hasMatch():
                start_index = match.capturedStart()
            else:
                start_index = -1

        while start_index >= 0:
            match = end_regex.match(text, start_index)
            if not match.hasMatch():
                # End not in this block, set state and highlight to end
                self.setCurrentBlockState(state)
                length = len(text) - start_index
                self.setFormat(start_index, length, format)
                break
            else:
                # End is in this block
                end_index = match.capturedStart()
                length = end_index - start_index + match.capturedLength()
                self.setFormat(start_index, length, format)
                
                # Check for another start after this end
                match = start_regex.match(text, start_index + length)
                if match.hasMatch():
                    start_index = match.capturedStart()
                else:
                    start_index = -1


class LineNumberArea(QWidget):
    """
    A widget to display line numbers for a QPlainTextEdit.
    """
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)


class PythonCodeEditor(QPlainTextEdit):
    """
    A QPlainTextEdit widget with line numbers and Python syntax highlighting.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup font
        font = QFont("Courier", 10)
        self.setFont(font)
        self.setTabStopDistance(QFontMetrics(font).horizontalAdvance(' ') * 4)

        # Line number area
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        # Syntax highlighter
        self.highlighter = PythonHighlighter(self.document())

        # Set dark theme palette
        self.set_dark_theme()

    def set_dark_theme(self):
        """
        Apply a dark color scheme to the editor.
        """
        palette = self.palette()
        palette.setColor(palette.ColorRole.Base, QColor("#1E1E1E"))
        palette.setColor(palette.ColorRole.Text, QColor("#D4D4D4"))
        self.setPalette(palette)

    def lineNumberAreaWidth(self):
        """
        Calculates the width needed for the line number area.
        """
        digits = 1
        max_count = max(1, self.blockCount())
        while max_count >= 10:
            max_count //= 10
            digits += 1
        
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        """
        Sets the width of the line number area.
        """
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        """
        Scrolls the line number area when the editor scrolls.
        """
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        """
        Updates the line number area's geometry on editor resize.
        """
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        """
        Paints the line numbers in the line number area.
        """
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#252526"))  # Margin background

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))  # Line number color
                painter.drawText(
                    0,
                    int(top),
                    self.line_number_area.width() - 3, # Right-align
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlightCurrentLine(self):
        """
        Highlights the line where the cursor is currently located.
        """
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2A2A2A")  # Current line background
            selection.format.setBackground(line_color)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)


# --- Executable for Testing ---

class MainWindow(QMainWindow):
    """
    Main window for testing the PythonCodeEditor widget.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Code Editor Widget Test")
        self.setGeometry(100, 100, 800, 600)

        self.editor = PythonCodeEditor(self)
        self.setCentralWidget(self.editor)

        # Add some sample code
        sample_code = """
import sys

# This is a comment
class MySampleClass:
    def __init__(self, name):
        self.name = name

    def greet(self):
        '''
        This is a multi-line docstring
        using triple single quotes.
        '''
        print(f"Hello, {self.name}!")

def main_function(x, y):
    \"\"\"
    This is another multi-line docstring
    using triple double quotes.
    \"\"\"
    if x > y and True:
        return x * 2
    elif x == 0:
        return None
    else:
        return y - 1

# --- Main execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    my_var = "Test String"
    number = 123
    
    my_obj = MySampleClass("PyQt6")
    my_obj.greet()
    
    main_function(10, 5)
"""
        self.editor.setPlainText(sample_code)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())