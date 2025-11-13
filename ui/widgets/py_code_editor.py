import sys
import re
import keyword
import builtins

from PyQt6.QtCore import QRegularExpression, Qt, QRect, QSize
from PyQt6.QtGui import (
    QColor,
    QTextCharFormat,
    QSyntaxHighlighter,
    QFont,
    QFontDatabase,
    QPalette,
    QTextCursor,
    QPainter,
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPlainTextEdit,
    QVBoxLayout,
)


class PythonHighlighter(QSyntaxHighlighter):
    """
    Advanced Python syntax highlighter for QPlainTextEdit.
    Features:
    - Keywords, builtins, numbers, operators, braces, decorators
    - Strings (single, double), triple-quoted strings, and docstrings
    - f-strings including nested placeholder regions
    - Function and class definitions (names highlighted)
    - Comments (with TODO/FIXME/NOTE/BUG emphasis)
    """

    # Block states for multi-line strings
    STATE_TRIPLE_SQ = 1
    STATE_TRIPLE_DQ = 2
    STATE_TRIPLE_SQ_F = 3
    STATE_TRIPLE_DQ_F = 4

    def __init__(self, document):
        super().__init__(document)
        self._init_formats()
        self._init_regex()

    def _init_formats(self):
        def mkfmt(color_hex, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_hex))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            if italic:
                fmt.setFontItalic(True)
            return fmt

        # Atom One Dark inspired palette
        self.fmt_keyword = mkfmt("#c678dd", bold=True)
        self.fmt_builtin = mkfmt("#56b6c2")
        self.fmt_number = mkfmt("#d19a66")
        self.fmt_string = mkfmt("#98c379")
        self.fmt_docstring = mkfmt("#9dcc8b", italic=True)
        self.fmt_comment = mkfmt("#5c6370", italic=True)
        self.fmt_todo = mkfmt("#e5c07b", bold=True)
        self.fmt_decorator = mkfmt("#c678dd")
        self.fmt_operator = mkfmt("#56b6c2")
        self.fmt_brace = mkfmt("#abb2bf", bold=True)
        self.fmt_defname = mkfmt("#61afef", bold=True)
        self.fmt_classname = mkfmt("#e5c07b", bold=True)
        self.fmt_self = mkfmt("#e06c75", italic=True)
        self.fmt_dunder = mkfmt("#e06c75", bold=True)
        self.fmt_fplaceholder = mkfmt("#e5c07b", bold=True)  # f-string expressions

    def _init_regex(self):
        # Keywords
        kw = sorted(set(keyword.kwlist), key=len, reverse=True)
        # Include match/case for Python 3.10 (already included in keyword.kwlist for 3.10+)
        kw_pattern = r"\b(?:%s)\b" % "|".join(re.escape(k) for k in kw)
        self.re_keyword = QRegularExpression(kw_pattern)

        # Builtins (exclude dunder/private)
        builtin_names = sorted(
            {n for n in dir(builtins) if not n.startswith("_")},
            key=len,
            reverse=True,
        )
        # Escape names that may have special regex chars (unlikely but safe)
        builtin_pattern = r"\b(?:%s)\b" % "|".join(re.escape(n) for n in builtin_names)
        self.re_builtin = QRegularExpression(builtin_pattern)

        # Numbers: int, float, hex, bin, oct, complex, underscores
        self.re_number = QRegularExpression(
            r"\b(?:0[xX][0-9A-Fa-f_]+|0[bB][01_]+|0[oO][0-7_]+|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?(?:[jJ])?)\b"
        )

        # Decorators
        self.re_decorator = QRegularExpression(r"@[A-Za-z_][\w.]*")

        # Operators and delimiters
        self.re_operator = QRegularExpression(
            r"(\+=|-=|\*=|/=|//=|%=|\*\*=|>>=|<<=|&=|\^=|\|=|:=|->|==|!=|<=|>=|<<|>>|\*\*|//|[+\-*/%&|\^~<>!=])"
        )
        self.re_brace = QRegularExpression(r"[\[\]\{\}\(\)]")

        # self and dunder
        self.re_self = QRegularExpression(r"\bself\b")
        self.re_dunder = QRegularExpression(r"\b__\w+__\b")

        # Function and class names
        self.re_funcdef = QRegularExpression(r"\b(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
        self.re_classdef = QRegularExpression(r"\bclass\s+([A-Za-z_]\w*)\s*(?:\(|:)")

        # Triple-quote markers (we'll search with str.find, but keep these for reference)
        self.triple_sq = "'''"
        self.triple_dq = '"""'

        # TODO/FIXME patterns inside comments
        self.re_todo = QRegularExpression(r"\b(?:TODO|FIXME|NOTE|BUG|HACK)\b")

    # Utility: check overlap with protected ranges
    @staticmethod
    def _overlaps(ranges, start, length):
        end = start + length
        for s, e in ranges:
            if start < e and end > s:
                return True
        return False

    @staticmethod
    def _add_range(ranges, start, end):
        if start < end:
            ranges.append((start, end))

    def highlightBlock(self, text: str) -> None:
        self.setCurrentBlockState(0)
        protected = []  # list of (start, end) ranges to avoid reformatting

        # 1) Continue multi-line triple-quoted strings from previous block if needed
        prev_state = self.previousBlockState()
        if prev_state in (
            self.STATE_TRIPLE_SQ,
            self.STATE_TRIPLE_DQ,
            self.STATE_TRIPLE_SQ_F,
            self.STATE_TRIPLE_DQ_F,
        ):
            is_f = prev_state in (self.STATE_TRIPLE_SQ_F, self.STATE_TRIPLE_DQ_F)
            delim = self.triple_sq if prev_state in (self.STATE_TRIPLE_SQ, self.STATE_TRIPLE_SQ_F) else self.triple_dq
            end_idx = text.find(delim)
            if end_idx == -1:
                # Entire line is still part of the multi-line string
                self.setFormat(0, len(text), self.fmt_docstring)
                self._add_range(protected, 0, len(text))
                if is_f:
                    self._highlight_fstring_placeholders(text, 0, len(text))
                self.setCurrentBlockState(prev_state)
                return
            else:
                # Close the multi-line string
                end_pos = end_idx + len(delim)
                self.setFormat(0, end_pos, self.fmt_docstring)
                self._add_range(protected, 0, end_pos)
                if is_f:
                    self._highlight_fstring_placeholders(text, 0, end_pos)
                # Continue processing after the closing delimiter
                cursor = end_pos
        else:
            cursor = 0

        # 2) Scan for triple-quoted strings opened/closed within this block
        pos = cursor
        out_state = 0
        while pos < len(text):
            idx_sq = text.find(self.triple_sq, pos)
            idx_dq = text.find(self.triple_dq, pos)
            candidates = [i for i in (idx_sq, idx_dq) if i != -1]
            if not candidates:
                break
            nxt = min(candidates)
            delim = self.triple_sq if nxt == idx_sq else self.triple_dq

            # Determine prefix letters immediately preceding the delimiter
            prefix_end = nxt
            prefix_start = prefix_end - 1
            while prefix_start >= 0 and text[prefix_start].isalpha():
                prefix_start -= 1
            prefix = text[prefix_start + 1 : prefix_end]
            valid_prefix = all(c.lower() in {"r", "b", "u", "f"} for c in prefix) and len(prefix) <= 3
            is_f = "f" in prefix.lower() if valid_prefix else False
            start_idx = (prefix_start + 1) if valid_prefix else nxt

            # Find closing delimiter
            end_idx = text.find(delim, nxt + 3)
            if end_idx == -1:
                # Multi-line starts here
                self.setFormat(start_idx, len(text) - start_idx, self.fmt_docstring)
                self._add_range(protected, start_idx, len(text))
                if is_f:
                    self._highlight_fstring_placeholders(text, start_idx, len(text))
                out_state = (
                    self.STATE_TRIPLE_SQ_F
                    if delim == self.triple_sq and is_f
                    else self.STATE_TRIPLE_DQ_F
                    if delim == self.triple_dq and is_f
                    else self.STATE_TRIPLE_SQ
                    if delim == self.triple_sq
                    else self.STATE_TRIPLE_DQ
                )
                pos = len(text)  # stop scanning further
                break
            else:
                end_pos = end_idx + len(delim)
                self.setFormat(start_idx, end_pos - start_idx, self.fmt_docstring)
                self._add_range(protected, start_idx, end_pos)
                if is_f:
                    self._highlight_fstring_placeholders(text, start_idx, end_pos)
                pos = end_pos

        if out_state:
            self.setCurrentBlockState(out_state)

        # 3) Single-line strings (with optional prefixes, including f-strings)
        self._highlight_single_line_strings(text, protected)

        # 4) Comments (ensure not inside strings)
        self._highlight_comments(text, protected)

        # 5) Tokens: keywords, builtins, numbers, operators, braces, decorators
        self._apply_regex(self.re_keyword, self.fmt_keyword, text, protected)
        self._apply_regex(self.re_builtin, self.fmt_builtin, text, protected)
        self._apply_regex(self.re_number, self.fmt_number, text, protected)
        self._apply_regex(self.re_decorator, self.fmt_decorator, text, protected)
        self._apply_regex(self.re_operator, self.fmt_operator, text, protected)
        self._apply_regex(self.re_brace, self.fmt_brace, text, protected)
        self._apply_regex(self.re_self, self.fmt_self, text, protected)
        self._apply_regex(self.re_dunder, self.fmt_dunder, text, protected)

        # 6) Function and class names (highlight captured group)
        self._apply_regex_group(self.re_funcdef, 1, self.fmt_defname, text, protected)
        self._apply_regex_group(self.re_classdef, 1, self.fmt_classname, text, protected)

    def _apply_regex(self, regex: QRegularExpression, fmt: QTextCharFormat, text: str, protected):
        it = regex.globalMatch(text)
        while it.hasNext():
            m = it.next()
            start = m.capturedStart()
            length = m.capturedLength()
            if not self._overlaps(protected, start, length):
                self.setFormat(start, length, fmt)

    def _apply_regex_group(self, regex: QRegularExpression, group: int, fmt: QTextCharFormat, text: str, protected):
        it = regex.globalMatch(text)
        while it.hasNext():
            m = it.next()
            start = m.capturedStart(group)
            length = m.capturedLength(group)
            if start >= 0 and length > 0 and not self._overlaps(protected, start, length):
                self.setFormat(start, length, fmt)

    def _highlight_comments(self, text: str, protected):
        idx = 0
        while idx < len(text):
            pos = text.find("#", idx)
            if pos == -1:
                break
            if self._overlaps(protected, pos, 1):
                idx = pos + 1
                continue
            # Everything till end of line is comment
            self.setFormat(pos, len(text) - pos, self.fmt_comment)
            self._add_range(protected, pos, len(text))

            # Emphasize TODO-like tags inside the comment
            m_iter = self.re_todo.globalMatch(text[pos:])
            while m_iter.hasNext():
                m = m_iter.next()
                s = pos + m.capturedStart()
                l = m.capturedLength()
                # Overlaps by definition, no need to check
                self.setFormat(s, l, self.fmt_todo)

            break  # rest of the line is comment

    def _highlight_single_line_strings(self, text: str, protected):
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch in ("'", '"'):
                # Skip triple quotes (already handled)
                if i + 2 < n and text[i : i + 3] in (self.triple_sq, self.triple_dq):
                    i += 3
                    continue
                # Check prefix letters immediately before this quote
                prefix_end = i
                prefix_start = prefix_end - 1
                while prefix_start >= 0 and text[prefix_start].isalpha():
                    prefix_start -= 1
                prefix = text[prefix_start + 1 : prefix_end]
                valid_prefix = all(c.lower() in {"r", "b", "u", "f"} for c in prefix) and len(prefix) <= 3
                start_idx = (prefix_start + 1) if valid_prefix else i
                is_f = "f" in prefix.lower() if valid_prefix else False
                is_raw = "r" in prefix.lower() if valid_prefix else False

                # If start_idx or i is inside protected region (e.g., part of a triple), skip
                if self._overlaps(protected, start_idx, 1):
                    i += 1
                    continue

                # Find closing quote
                j = i + 1
                while j < n:
                    c = text[j]
                    if not is_raw and c == "\\":
                        # Skip escaped char
                        j += 2
                        continue
                    if c == ch:
                        break
                    j += 1
                end_idx = j if j < n else n - 1
                length = (end_idx - start_idx) + 1
                if length <= 0:
                    i += 1
                    continue
                self.setFormat(start_idx, length, self.fmt_string)
                self._add_range(protected, start_idx, start_idx + length)

                if is_f:
                    self._highlight_fstring_placeholders(text, start_idx, start_idx + length)

                i = end_idx + 1
            else:
                i += 1

    def _highlight_fstring_placeholders(self, text: str, start: int, end: int):
        """
        Highlight { ... } placeholder regions inside an f-string range [start, end).
        Handles nested braces and ignores doubled braces {{ and }}.
        """
        i = start
        # Attempt to skip the optional prefix letters and opening quote(s)
        # Find first quote character within the region to begin scanning expressions after it
        # Start scanning after the first quote char inside [start, end)
        j = start
        # Skip possible prefix letters
        while j < end and text[j].isalpha():
            j += 1
        # Skip one or three starting quotes if present
        if j + 2 < end and text[j : j + 3] in (self.triple_sq, self.triple_dq):
            scan_start = j + 3
        elif j < end and text[j] in ("'", '"'):
            scan_start = j + 1
        else:
            scan_start = start  # fallback

        i = scan_start
        while i < end:
            if text[i] == "{":
                # Handle escaped '{{'
                if i + 1 < end and text[i + 1] == "{":
                    i += 2
                    continue
                depth = 1
                k = i + 1
                while k < end and depth > 0:
                    if text[k] == "{":
                        if not (k + 1 < end and text[k + 1] == "{"):
                            depth += 1
                            k += 1
                            continue
                        else:
                            k += 2
                            continue
                    elif text[k] == "}":
                        if not (k + 1 < end and text[k + 1] == "}"):
                            depth -= 1
                            k += 1
                            continue
                        else:
                            k += 2
                            continue
                    else:
                        k += 1
                placeholder_end = min(k, end)
                if placeholder_end > i:
                    self.setFormat(i, placeholder_end - i, self.fmt_fplaceholder)
                i = placeholder_end
            elif text[i] == "}":
                # Handle escaped '}}'
                if i + 1 < end and text[i + 1] == "}":
                    i += 2
                else:
                    i += 1
            else:
                i += 1


class PythonEditorWidget(QWidget):
    """
    Standalone Python code editor widget with advanced syntax highlighting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = CodeEditor(self)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Monospaced font
        try:
            fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        except Exception:
            fixed = QFont("Monospace")
            fixed.setStyleHint(QFont.StyleHint.TypeWriter)
        fixed.setPointSize(fixed.pointSize() + 1)
        self.editor.setFont(fixed)

        self._apply_atom_one_dark_theme()

        layout.addWidget(self.editor)

        # Attach highlighter
        self.highlighter = PythonHighlighter(self.editor.document())

        self.setLayout(layout)
        self.setWindowTitle("Python Editor Widget")

    # Convenience methods (optional)
    def setText(self, text: str):
        self.editor.setPlainText(text)

    def text(self) -> str:
        return self.editor.toPlainText()

    def _apply_atom_one_dark_theme(self):
        palette = self.editor.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#282c34"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#abb2bf"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3e4451"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#5c6370"))
        palette.setColor(QPalette.ColorRole.Window, QColor("#282c34"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#abb2bf"))
        self.editor.setPalette(palette)
        self.editor.setStyleSheet(
            "QPlainTextEdit {"
            "background-color: #282c34;"
            "color: #abb2bf;"
            "selection-color: #ffffff;"
            "selection-background-color: #3e4451;"
            "}"
        )


class LineNumberArea(QWidget):
    """Line number display widget for CodeEditor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Lightweight conveniences for typing Python."""

    INDENT = " " * 4
    MIN_FONT_SIZE = 6
    MAX_FONT_SIZE = 48

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        modifiers = event.modifiers()

        if self._handle_pair_chars(text, modifiers):
            event.accept()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._handle_newline()
            event.accept()
            return

        if key == Qt.Key.Key_Tab:
            self._insert_text(self.INDENT)
            event.accept()
            return

        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta != 0:
                step = 1 if delta > 0 else -1
                self._change_font_size(step)
            event.accept()
            return
        super().wheelEvent(event)

    def _handle_pair_chars(self, text: str, modifiers) -> bool:
        # Ignore if control/alt modifiers involved
        blocked = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        if modifiers & blocked:
            return False

        pairs = {
            '"': '"',
            "(": ")",
        }

        if text not in pairs:
            return False

        open_char = text
        close_char = pairs[text]
        cursor = self.textCursor()

        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"{open_char}{selected}{close_char}")
            new_pos = cursor.position()
            cursor.setPosition(new_pos - len(selected) - 1)
            cursor.setPosition(new_pos - 1, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
            return True

        next_char = self._char_after_cursor(cursor)
        if next_char == close_char:
            cursor.movePosition(QTextCursor.MoveOperation.NextCharacter)
            self.setTextCursor(cursor)
            return True

        cursor.insertText(f"{open_char}{close_char}")
        cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter)
        self.setTextCursor(cursor)
        return True

    def _handle_newline(self):
        cursor = self.textCursor()
        current_line = cursor.block().text()
        position_in_block = cursor.positionInBlock()
        line_to_cursor = current_line[:position_in_block]
        base_indent_match = re.match(r"\s*", current_line)
        base_indent = base_indent_match.group(0) if base_indent_match else ""
        extra_indent = self.INDENT if line_to_cursor.rstrip().endswith(":") else ""

        cursor.beginEditBlock()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertBlock()
        cursor.insertText(base_indent + extra_indent)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _insert_text(self, value: str):
        cursor = self.textCursor()
        cursor.insertText(value)
        self.setTextCursor(cursor)

    def _char_after_cursor(self, cursor: QTextCursor) -> str:
        doc = self.document()
        pos = cursor.position()
        if pos >= doc.characterCount():
            return ""
        ch = doc.characterAt(pos)
        if not ch or ch == "\x00":
            return ""
        return ch

    def _change_font_size(self, step: int):
        font = self.font()
        current_size = font.pointSize()
        if current_size <= 0:
            current_size = self.fontMetrics().height()
        new_size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, current_size + step))
        if new_size == current_size:
            return
        font.setPointSize(new_size)
        self.setFont(font)
        self.document().setDefaultFont(font)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 20 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#21252b"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#5c6370"))
                painter.drawText(0, int(top), self.line_number_area.width() - 12, self.fontMetrics().height(),
                                Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = PythonEditorWidget()
    widget.show()
    sys.exit(app.exec())