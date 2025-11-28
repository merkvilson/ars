from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QKeyEvent
from PyQt6.QtCore import QRegularExpression, Qt 
from PyQt6.QtWidgets import QPlainTextEdit

from .editor import BaseCodeEditor
import webcolors
import re

class PromptHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        
        # Hex codes pattern
        self.hex_pattern = QRegularExpression(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
        
        # Color names from webcolors (CSS3)
        # Use public API to get names and build map
        try:
            # webcolors >= 1.11 uses names() function
            names = webcolors.names("css3")
            self.color_map = {name: webcolors.name_to_hex(name) for name in names}
        except (AttributeError, TypeError):
            # Fallback for older versions or if names() is not available/different
            try:
                self.color_map = webcolors.CSS3_NAMES_TO_HEX
            except AttributeError:
                # Fallback to basic QColor names if webcolors fails completely
                self.color_map = {name: name for name in QColor.colorNames()}

        self.color_names = list(self.color_map.keys())
        
        # Regex for color names (word boundary)
        # Sort by length descending to match longest names first (e.g. "darkblue" before "blue")
        sorted_colors = sorted(self.color_names, key=len, reverse=True)
        
        # Build regex pattern
        pattern = r"\b(" + "|".join(re.escape(c) for c in sorted_colors) + r")\b"
        self.color_pattern = QRegularExpression(pattern)
        self.color_pattern.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)

    def highlightBlock(self, text):
        # 1. Highlight Hex Codes
        match_iter = self.hex_pattern.globalMatch(text)
        while match_iter.hasNext():
            match = match_iter.next()
            color_str = match.captured(0)
            
            fmt = QTextCharFormat()
            if QColor.isValidColor(color_str):
                fmt.setForeground(QColor(color_str))
            fmt.setFontWeight(QFont.Weight.Bold)
            
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # 2. Highlight Color Names
        match_iter = self.color_pattern.globalMatch(text)
        while match_iter.hasNext():
            match = match_iter.next()
            color_name = match.captured(1).lower()
            
            if color_name in self.color_map:
                hex_value = self.color_map[color_name]
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(hex_value))
                fmt.setFontWeight(QFont.Weight.Bold)
                
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class PromptEditor(BaseCodeEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = PromptHighlighter(self.document())
        
        # Hide line numbers by default for prompt editor
        self.set_line_numbers_visible(False)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        
        # Set a default font that might be more suitable for prompts (optional)
        # For now, we stick to the base class font (Consolas/Monospace)
        
    def change_selection_font_size(self, delta):
        """Change the font size of the current selection."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        # Get current format
        fmt = cursor.charFormat()
        current_size = fmt.fontPointSize()
        
        # If point size is not set (0), use the default font size
        if current_size <= 0:
            current_size = self.font().pointSize()
            
        new_size = max(6, current_size + delta)
        
        fmt.setFontPointSize(new_size)
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event: QKeyEvent):
        modifiers = event.modifiers()
        key = event.key()

        # Alt + Plus/Minus to change selection font size
        if modifiers & Qt.KeyboardModifier.AltModifier:
            if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.change_selection_font_size(1)
                event.accept()
                return
            elif key in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
                self.change_selection_font_size(-1)
                event.accept()
                return

        super().keyPressEvent(event)

    def _get_completions(self, text, pos_in_block, current_word):
        # Base completions (icons)
        completions = super()._get_completions(text, pos_in_block, current_word)
        
        # Add color completions
        if current_word:
            # We can use the highlighter's color list
            for color in self.highlighter.color_names:
                if color.lower().startswith(current_word.lower()):
                    # (name, type, signature, icon_char)
                    # We use 'instance' type color for the popup
                    completions.append((color, 'instance', '', None))
        
        return completions
