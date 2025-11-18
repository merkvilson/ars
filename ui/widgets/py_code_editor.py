import sys
import re
import keyword
import builtins

try:
    import jedi
    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False
    print("Warning: jedi not available. Autocompletion will be disabled.")

from PyQt6.QtCore import QRegularExpression, Qt, QRect, QSize, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QTextCharFormat,
    QSyntaxHighlighter,
    QFont,
    QTextCursor,
    QPainter,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPlainTextEdit,
    QVBoxLayout,
)    
try: 
    from ars_cmds.core_cmds.run_ext import run_string_code
    STANDALONE = False
except ImportError:
    print("executing py_code_editor.py in __main__ mode")
    STANDALONE = True
    
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
        self.fmt_builtin = mkfmt("#c25656")
        self.fmt_number = mkfmt("#d16666")
        self.fmt_string = mkfmt("#98c379")
        self.fmt_string_prefix = mkfmt("#56b6c2", bold=True, italic=True)  # r, f, b, u prefixes
        self.fmt_docstring = mkfmt("#9dcc8b", italic=True)
        self.fmt_comment = mkfmt("#5c6370", italic=True)
        self.fmt_todo = mkfmt("#e5c07b", bold=True)
        self.fmt_decorator = mkfmt("#c678dd")
        self.fmt_operator = mkfmt("#00e1ff")
        self.fmt_brace = mkfmt("#e5c07b", bold=True)
        self.fmt_defname = mkfmt("#61afef", bold=True)
        self.fmt_classname = mkfmt("#e5c07b", bold=True)
        self.fmt_self = mkfmt("#e06c75", italic=True)
        self.fmt_dunder = mkfmt("#e06c75", bold=True)
        self.fmt_magic = mkfmt("#c678dd", bold=True)  # magic methods like __init__
        self.fmt_boolean = mkfmt("#d19a66", bold=True)  # True, False, None
        self.fmt_function_call = mkfmt("#61afef")  # function calls
        self.fmt_class_instantiation = mkfmt("#e5c07b")  # MyClass()
        self.fmt_parameter = mkfmt("#d19a66")  # function parameters
        self.fmt_lambda = mkfmt("#c678dd", italic=True)  # lambda keyword
        self.fmt_fplaceholder = mkfmt("#e5c07b", bold=True)  # f-string expressions

    def _init_regex(self):
        # Keywords (excluding True, False, None which we'll handle separately)
        kw = sorted(set(keyword.kwlist) - {'True', 'False', 'None'}, key=len, reverse=True)
        kw_pattern = r"\b(?:%s)\b" % "|".join(re.escape(k) for k in kw)
        self.re_keyword = QRegularExpression(kw_pattern)

        # Boolean and None literals
        self.re_boolean = QRegularExpression(r"\b(?:True|False|None)\b")

        # Lambda keyword (separate from other keywords)
        self.re_lambda = QRegularExpression(r"\blambda\b")

        # Builtins (exclude dunder/private, True, False, None)
        builtin_names = sorted(
            {n for n in dir(builtins) if not n.startswith("_") and n not in {'True', 'False', 'None'}},
            key=len,
            reverse=True,
        )
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

        # self and cls
        self.re_self = QRegularExpression(r"\b(?:self|cls)\b")
        
        # Magic methods (__init__, __str__, etc.) - more specific than general dunder
        self.re_magic = QRegularExpression(r"\b__(?:init|new|del|repr|str|bytes|format|lt|le|eq|ne|gt|ge|hash|bool|dir|get|set|delete|set_name|init_subclass|call|len|length_hint|getitem|setitem|delitem|missing|iter|reversed|contains|add|sub|mul|matmul|truediv|floordiv|mod|divmod|pow|lshift|rshift|and|xor|or|neg|pos|abs|invert|complex|int|float|index|round|trunc|floor|ceil|enter|exit|await|aiter|anext|aenter|aexit)__\b")
        
        # General dunder (for other double underscore names)
        self.re_dunder = QRegularExpression(r"\b__\w+__\b")

        # Function and class definitions
        self.re_funcdef = QRegularExpression(r"\b(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
        self.re_classdef = QRegularExpression(r"\bclass\s+([A-Za-z_]\w*)\s*(?:\(|:)")
        
        # Function calls: identifier followed by (
        self.re_function_call = QRegularExpression(r"\b([A-Za-z_]\w*)\s*(?=\()")
        
        # Class instantiation: capitalized identifier followed by (
        self.re_class_instantiation = QRegularExpression(r"\b([A-Z][A-Za-z0-9_]*)\s*(?=\()")
        
        # Function parameters: in def signature between ( and )
        self.re_parameter = QRegularExpression(r"\(\s*([A-Za-z_]\w*)")

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

        # 2) Single-line strings FIRST (with optional prefixes, including f-strings)
        # This prevents triple quotes inside strings from being misdetected
        self._highlight_single_line_strings(text, protected)

        # 3) Scan for triple-quoted strings opened/closed within this block
        # Only scan areas not already protected by single-line strings
        pos = cursor
        out_state = 0
        while pos < len(text):
            # Skip positions already in protected ranges
            if self._overlaps(protected, pos, 1):
                pos += 1
                continue
                
            idx_sq = text.find(self.triple_sq, pos)
            idx_dq = text.find(self.triple_dq, pos)
            candidates = [i for i in (idx_sq, idx_dq) if i != -1 and not self._overlaps(protected, i, 3)]
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
                # Highlight prefix after docstring format (so it doesn't get overwritten)
                if valid_prefix and prefix:
                    self.setFormat(prefix_start + 1, len(prefix), self.fmt_string_prefix)
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
                # Highlight prefix after docstring format (so it doesn't get overwritten)
                if valid_prefix and prefix:
                    self.setFormat(prefix_start + 1, len(prefix), self.fmt_string_prefix)
                self._add_range(protected, start_idx, end_pos)
                if is_f:
                    self._highlight_fstring_placeholders(text, start_idx, end_pos)
                pos = end_pos

        if out_state:
            self.setCurrentBlockState(out_state)

        # 4) Comments (ensure not inside strings)
        self._highlight_comments(text, protected)

        # 5) Tokens: keywords, builtins, numbers, operators, braces, decorators
        self._apply_regex(self.re_keyword, self.fmt_keyword, text, protected)
        self._apply_regex(self.re_lambda, self.fmt_lambda, text, protected)
        self._apply_regex(self.re_boolean, self.fmt_boolean, text, protected)
        self._apply_regex(self.re_builtin, self.fmt_builtin, text, protected)
        self._apply_regex(self.re_number, self.fmt_number, text, protected)
        self._apply_regex(self.re_decorator, self.fmt_decorator, text, protected)
        self._apply_regex(self.re_operator, self.fmt_operator, text, protected)
        self._apply_regex(self.re_brace, self.fmt_brace, text, protected)
        self._apply_regex(self.re_self, self.fmt_self, text, protected)
        self._apply_regex(self.re_magic, self.fmt_magic, text, protected)
        self._apply_regex(self.re_dunder, self.fmt_dunder, text, protected)

        # 6) Function and class definitions (highlight captured group)
        self._apply_regex_group(self.re_funcdef, 1, self.fmt_defname, text, protected)
        self._apply_regex_group(self.re_classdef, 1, self.fmt_classname, text, protected)
        
        # 7) Function calls and class instantiation
        self._apply_regex_group(self.re_class_instantiation, 1, self.fmt_class_instantiation, text, protected)
        self._apply_regex_group(self.re_function_call, 1, self.fmt_function_call, text, protected)

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
                
                # Highlight the string (from start_idx which may include prefix)
                self.setFormat(start_idx, length, self.fmt_string)
                
                # Highlight string prefix AFTER the string (so it doesn't get overwritten)
                if valid_prefix and prefix:
                    self.setFormat(prefix_start + 1, len(prefix), self.fmt_string_prefix)
                
                self._add_range(protected, start_idx, start_idx + length)

                if is_f:
                    self._highlight_fstring_placeholders(text, start_idx, start_idx + length)

                i = end_idx + 1
            else:
                i += 1

    def _highlight_fstring_placeholders(self, text: str, start: int, end: int):
        """
        Clear string formatting inside { } placeholders and highlight only the braces.
        """
        j = start
        # Skip possible prefix letters
        while j < end and text[j].isalpha():
            j += 1
        # Skip opening quotes
        if j + 2 < end and text[j : j + 3] in (self.triple_sq, self.triple_dq):
            scan_start = j + 3
        elif j < end and text[j] in ("'", '"'):
            scan_start = j + 1
        else:
            scan_start = start

        i = scan_start
        while i < end:
            if text[i] == "{":
                if i + 1 < end and text[i + 1] == "{":  # Escaped {{
                    i += 2
                    continue
                
                # Highlight opening brace
                self.setFormat(i, 1, self.fmt_fplaceholder)
                depth = 1
                k = i + 1
                content_start = k
                
                while k < end and depth > 0:
                    if text[k] == "{" and not (k + 1 < end and text[k + 1] == "{"):
                        depth += 1
                        k += 1
                    elif text[k] == "}" and not (k + 1 < end and text[k + 1] == "}"):
                        depth -= 1
                        if depth == 0:
                            # Clear formatting on content, highlight closing brace
                            if k > content_start:
                                self.setFormat(content_start, k - content_start, QTextCharFormat())
                            self.setFormat(k, 1, self.fmt_fplaceholder)
                        k += 1
                    else:
                        if text[k : k + 2] in ("{{", "}}"):
                            k += 2
                        else:
                            k += 1
                i = k
            else:
                i += 1


class JediCompleter:
    """Wrapper around Jedi for Python autocompletion."""
    
    def __init__(self):
        self.enabled = JEDI_AVAILABLE
        self.namespace = {}
    
    def set_namespace(self, namespace_dict):
        """Set custom namespace for completions (e.g., injected variables)."""
        self.namespace = namespace_dict or {}
    
    def get_completions(self, source_code, line, column, file_path=None, namespace=None):
        """
        Get completion suggestions at the given position.
        
        Args:
            source_code: Full text of the document
            line: 1-based line number
            column: 0-based column number
            file_path: Optional path for better context
            namespace: Optional dict of runtime objects to include in completions
            
        Returns:
            List of tuples: (name, type, signature)
        """
        if not self.enabled:
            return []
        
        # Use provided namespace or fall back to stored namespace
        ns = namespace if namespace is not None else self.namespace
        
        try:
            # Use Interpreter if we have a namespace, otherwise use Script
            if ns:
                interpreter = jedi.Interpreter(code=source_code, namespaces=[ns])
                completions = interpreter.complete(line, column)
            else:
                script = jedi.Script(code=source_code, path=file_path)
                completions = script.complete(line, column)
            
            results = []
            for c in completions:
                # Get completion type (function, module, class, etc.)
                comp_type = c.type
                
                # Get signature for functions/methods
                signature = ""
                if comp_type in ('function', 'method'):
                    try:
                        signatures = c.get_signatures()
                        if signatures:
                            sig = signatures[0]
                            params = [p.name for p in sig.params if p.name not in ('self', 'cls')]
                            signature = f"({', '.join(params)})"
                    except:
                        signature = "()"
                
                results.append((c.name, comp_type, signature))
            
            return results[:50]  # Limit to 50 suggestions
        except Exception as e:
            # Silently fail - don't interrupt typing
            return []


class CompletionPopup(QWidget):
    """Popup widget displaying autocompletion suggestions."""
    
    completion_selected = pyqtSignal(str)  # Emitted when user selects a completion
    
    def __init__(self, parent=None):
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        # Use ToolTip window type - it never steals focus!
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        
        # Critical: Don't take focus from the editor!
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        
        # Styling
        self.setStyleSheet("""
            CompletionPopup {
                background-color: #1e2127;
                border: 1px solid #4b5263;
                border-radius: 4px;
            }
            QListWidget {
                background-color: #1e2127;
                color: #abb2bf;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 8px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #3e4451;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2c313c;
            }
        """)
        
        self.completions_data = []  # Store (name, type, signature) tuples
        # Don't set fixed size - will resize dynamically
    
    def set_editor_font(self, font):
        """Update the font to match the editor."""
        self.list_widget.setFont(font)
    
    def set_completions(self, completions):
        """
        Set completion items.
        
        Args:
            completions: List of tuples (name, type, signature)
        """
        from PyQt6.QtWidgets import QListWidgetItem
        from PyQt6.QtGui import QIcon, QPixmap, QPainter
        
        self.list_widget.clear()
        self.completions_data = completions
        
        # Type icons/colors
        type_colors = {
            'function': '#61afef',
            'method': '#61afef',
            'class': '#e5c07b',
            'module': '#c678dd',
            'instance': '#98c379',
            'keyword': '#c678dd',
            'statement': '#c678dd',
            'param': '#d19a66',
        }
        
        type_symbols = {
            'function': 'ƒ',
            'method': 'm',
            'class': 'C',
            'module': 'M',
            'instance': 'v',
            'keyword': 'K',
            'statement': 'S',
            'param': 'p',
        }

        for name, comp_type, signature in completions:
            color = type_colors.get(comp_type, '#abb2bf')
            symbol = type_symbols.get(comp_type, '•')
            
            # Format display text
            display = f"  {symbol}  {name}{signature}"
            
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, name)  # Store actual completion text
            
            # Color the type symbol
            # (Note: QListWidget doesn't support rich text easily, so we use uniform coloring)
            self.list_widget.addItem(item)
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        
        # Resize to fit content
        self._adjust_size()
    
    def _adjust_size(self):
        """Resize the popup to fit the content."""
        if self.list_widget.count() == 0:
            return
        
        # Calculate required height based on number of items
        item_count = self.list_widget.count()
        max_visible_items = 10  # Show max 10 items before scrolling
        visible_items = min(item_count, max_visible_items)
        
        # Get height of one item
        item_height = self.list_widget.sizeHintForRow(0)
        total_height = item_height * visible_items + 4  # +4 for borders
        
        # Calculate required width based on longest item
        max_width = 0
        for i in range(item_count):
            item = self.list_widget.item(i)
            if item:
                text_width = self.list_widget.fontMetrics().horizontalAdvance(item.text())
                max_width = max(max_width, text_width)
        
        # Add padding for icon, scrollbar, and margins
        total_width = max_width + 40
        total_width = max(200, min(600, total_width))  # Min 200, max 600
        
        self.resize(total_width, total_height)
    
    def current_completion(self):
        """Get the currently selected completion text."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def select_next(self):
        """Move selection down."""
        current = self.list_widget.currentRow()
        if current < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(current + 1)
    
    def select_previous(self):
        """Move selection up."""
        current = self.list_widget.currentRow()
        if current > 0:
            self.list_widget.setCurrentRow(current - 1)
    
    def _on_item_clicked(self, item):
        """Handle item click."""
        completion = item.data(Qt.ItemDataRole.UserRole)
        if completion:
            self.completion_selected.emit(completion)
            self.hide()


class LineNumberArea(QWidget):
    """Line number display widget for CodeEditor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Lightweight conveniences for typing Python."""

    INDENT = " " * 4
    MIN_FONT_SIZE = 10
    MAX_FONT_SIZE = 48
    DEFAULT_FONT_SIZE = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.line_number_area.setFont(self.font())

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)
        self.custom_namespace = {}
        self.project_file_path = None
        
        # Autocompletion setup
        self.completer = JediCompleter()
        self.completion_popup = CompletionPopup(self)
        self.completion_popup.completion_selected.connect(self._insert_completion)
        self.completion_popup.hide()
        self._completion_active = False

        # Monospaced font - use Consolas (common on Windows) or Courier New
        fixed = QFont("Consolas", 14)
        fixed.setWeight(QFont.Weight.Medium)
        self.setFont(fixed)
        self.completion_popup.set_editor_font(fixed)

        # Attach highlighter
        self.highlighter = PythonHighlighter(self.document())


        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setStyleSheet(
            "QPlainTextEdit {"
            f"background-color: rgba(40, 44, 52, {1.0 if STANDALONE else 0.55});"            "color: #abb2bf;"
            "border: none;"
            "border-radius: 20px;"
            "selection-color: #ffffff;"
            "selection-background-color: #3e4451;"
            "}"
        )



    def setFont(self, font):
        """Override setFont to keep line number area and completion popup in sync."""
        super().setFont(font)
        if hasattr(self, 'line_number_area'):
            self.line_number_area.setFont(font)
            self.update_line_number_area_width(0)
        if hasattr(self, 'completion_popup'):
            self.completion_popup.set_editor_font(font)

    def run_code(self, namespace_injection=None):
        if namespace_injection is None: namespace_injection = self.custom_namespace
        if not STANDALONE: run_string_code(self.toPlainText(), namespace_injection)
        else: exec(self.toPlainText())


    def save_script(self):
        with open(self.project_file_path, 'w', encoding='utf-8') as f:
            f.write(self.toPlainText())


    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        modifiers = event.modifiers()
        
        # Handle completion popup navigation - ONLY specific keys when popup is visible
        if self._completion_active and self.completion_popup.isVisible():
            # Up/Down arrow keys for navigation
            if key == Qt.Key.Key_Down:
                self.completion_popup.select_next()
                event.accept()
                return
            elif key == Qt.Key.Key_Up:
                self.completion_popup.select_previous()
                event.accept()
                return
            # Escape to dismiss
            elif key == Qt.Key.Key_Escape:
                self.completion_popup.hide()
                self._completion_active = False
                event.accept()
                return
            # Tab to accept (only if no modifiers and no selection)
            elif key == Qt.Key.Key_Tab and not modifiers and not self.textCursor().hasSelection():
                self._accept_completion()
                event.accept()
                return
            # Enter to accept (only if no modifiers)
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not modifiers:
                self._accept_completion()
                event.accept()
                return
            # For ALL other keys, let them pass through normally

        if self._handle_pair_chars(text, modifiers):
            event.accept()
            return

        if key == Qt.Key.Key_R and modifiers & Qt.KeyboardModifier.ControlModifier:
            self.run_code(self.custom_namespace)
            event.accept()
            return
        
        if key == Qt.Key.Key_S and modifiers & Qt.KeyboardModifier.ControlModifier:
            if self.project_file_path:
                self.save_script()
            event.accept()
            return

        if key == Qt.Key.Key_Slash and modifiers & Qt.KeyboardModifier.ControlModifier:
            self._toggle_comment()
            event.accept()
            return

        if key == Qt.Key.Key_D and modifiers & Qt.KeyboardModifier.ControlModifier:
            self._duplicate_line()
            event.accept()
            return

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key in (
                Qt.Key.Key_Plus,
                Qt.Key.Key_Equal,
                Qt.Key.Key_BracketRight,
            ):
                self._change_font_size(1)
                event.accept()
                return
            if key in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore, Qt.Key.Key_BracketLeft):
                self._change_font_size(-1)
                event.accept()
                return
            if key == Qt.Key.Key_0:
                self._reset_font_size()
                event.accept()
                return

        if (
            key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and modifiers & Qt.KeyboardModifier.ControlModifier
        ):
            self._insert_line_below()
            event.accept()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Hide completion popup on Enter
            if self._completion_active:
                self.completion_popup.hide()
                self._completion_active = False
            self._handle_newline()
            event.accept()
            return

        if key == Qt.Key.Key_Backspace and not modifiers:
            if self._handle_smart_backspace():
                # Update completions after backspace if popup was active
                if self._completion_active:
                    self._trigger_completion()
                event.accept()
                return

        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier) or key == Qt.Key.Key_Backtab
            is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
            if is_shift:
                self._adjust_selection_indent(decrease=True)
            elif is_ctrl:
                self._add_indent_at_line_start()
            else:
                if self.textCursor().hasSelection():
                    self._adjust_selection_indent(decrease=False)
                else:
                    self._insert_text(self.INDENT)
            event.accept()
            return

        # Call parent to handle the key first
        super().keyPressEvent(event)
        
        # After handling the key, manage completion popup
        if text and (text.isalnum() or text in ('_', '.')):
            # Continue showing/updating completions for valid identifier characters
            self._trigger_completion()
        elif text and self._completion_active:
            # Hide completion for other printable characters
            self.completion_popup.hide()
            self._completion_active = False

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
        
        # Expandable pairing map keeps behavior centralized
        pairs = {
            '"': '"',
            "'": "'",
            "(": ")",
            "[": "]",
            "{": "}",
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

    def _toggle_comment(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)

        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()

        doc = self.document()
        start_block = doc.findBlock(selection_start)
        # Ensure we include the block where the selection ends when caret is at column 0
        end_index = max(selection_start, selection_end - 1)
        end_block = doc.findBlock(end_index)

        block = start_block
        should_comment = False
        while block.isValid():
            text = block.text()
            stripped = text.lstrip()
            if stripped and not stripped.startswith("#"):
                should_comment = True
                break
            if block == end_block:
                break
            block = block.next()

        edit_cursor = QTextCursor(doc)
        edit_cursor.beginEditBlock()

        block = start_block
        while block.isValid():
            text = block.text()
            indent_len = len(text) - len(text.lstrip())
            block_cursor = QTextCursor(doc)
            block_cursor.setPosition(block.position())
            block_cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.MoveAnchor,
                indent_len,
            )

            if should_comment:
                if text.strip():
                    block_cursor.insertText("# ")
            else:
                remainder = text[indent_len:]
                if remainder.startswith("# "):
                    block_cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        2,
                    )
                    block_cursor.removeSelectedText()
                elif remainder.startswith("#"):
                    block_cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        1,
                    )
                    block_cursor.removeSelectedText()

            if block == end_block:
                break
            block = block.next()

        edit_cursor.endEditBlock()

        new_cursor = self.textCursor()
        new_cursor.setPosition(start_block.position())
        new_cursor.setPosition(
            end_block.position() + end_block.length() - 1,
            QTextCursor.MoveMode.KeepAnchor,
        )
        self.setTextCursor(new_cursor)

    def _duplicate_line(self):
        """Duplicate current line or selected lines."""
        cursor = self.textCursor()
        doc = self.document()
        
        if cursor.hasSelection():
            # Duplicate selected lines
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
            
            start_block = doc.findBlock(selection_start)
            end_block = doc.findBlock(selection_end - 1 if selection_end > selection_start else selection_end)
            
            # Collect all text from selected blocks
            lines_text = []
            block = start_block
            while block.isValid():
                lines_text.append(block.text())
                if block == end_block:
                    break
                block = block.next()
            
            # Insert duplicated lines after the last selected block
            cursor.beginEditBlock()
            cursor.setPosition(end_block.position() + end_block.length() - 1)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            for line_text in lines_text:
                cursor.insertBlock()
                cursor.insertText(line_text)
            cursor.endEditBlock()
            
            # Select the newly duplicated lines
            new_start = end_block.position() + end_block.length()
            new_cursor = QTextCursor(doc)
            new_cursor.setPosition(new_start)
            # Move to end of last duplicated line
            for _ in range(len(lines_text) - 1):
                new_cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
            new_cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            end_pos = new_cursor.position()
            new_cursor.setPosition(new_start)
            new_cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(new_cursor)
        else:
            # Duplicate single line
            current_block = cursor.block()
            line_text = current_block.text()
            
            cursor.beginEditBlock()
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertBlock()
            cursor.insertText(line_text)
            cursor.endEditBlock()
            self.setTextCursor(cursor)

    def _handle_smart_backspace(self) -> bool:
        """
        Handle smart backspace for:
        1. Paired symbol deletion - if cursor is between matching pairs, delete both
        2. Indentation - delete in blocks of 4 spaces when in leading whitespace
        Returns True if handled, False to use default behavior
        """
        cursor = self.textCursor()
        
        # Don't handle if there's a selection
        if cursor.hasSelection():
            return False
        
        # Check for paired symbol deletion first
        pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        pos = cursor.position()
        doc = self.document()
        
        # Get character before and after cursor
        char_before = doc.characterAt(pos - 1) if pos > 0 else ''
        char_after = doc.characterAt(pos) if pos < doc.characterCount() else ''
        
        # If we're between a matching pair, delete both
        if char_before in pairs and pairs[char_before] == char_after:
            cursor.beginEditBlock()
            cursor.deletePreviousChar()  # Delete opening character
            cursor.deleteChar()  # Delete closing character
            cursor.endEditBlock()
            return True
        
        # Handle indentation deletion
        block = cursor.block()
        text = block.text()
        pos_in_block = cursor.positionInBlock()
        
        # If cursor is at the start of line, use default behavior
        if pos_in_block == 0:
            return False
        
        # Get text to the left of cursor
        text_before_cursor = text[:pos_in_block]
        
        # Check if we're only in leading whitespace (only spaces before cursor)
        if not text_before_cursor or not all(c == ' ' for c in text_before_cursor):
            return False
        
        # Count spaces before cursor
        space_count = len(text_before_cursor)
        
        # Determine how many spaces to remove
        if space_count % 4 == 0:
            # Divisible by 4: remove exactly 4 spaces
            chars_to_remove = 4
        else:
            # Not divisible by 4: remove to align to nearest 4-space boundary
            chars_to_remove = space_count % 4
        
        # Perform the deletion
        cursor.beginEditBlock()
        cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.KeepAnchor,
            chars_to_remove
        )
        cursor.removeSelectedText()
        cursor.endEditBlock()
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

    def _adjust_selection_indent(self, decrease: bool):
        cursor = self.textCursor()
        doc = self.document()

        has_selection = cursor.hasSelection()
        sel_start = cursor.selectionStart() if has_selection else cursor.position()
        sel_end = cursor.selectionEnd() if has_selection else cursor.position()

        start_block = doc.findBlock(sel_start)
        end_index = max(sel_start, sel_end - 1)
        end_block = doc.findBlock(end_index)

        caret_block_number = cursor.block().blockNumber()
        caret_column = cursor.position() - cursor.block().position()
        removed_on_caret_line = 0

        cursor.beginEditBlock()

        block = start_block
        while block.isValid():
            block_cursor = QTextCursor(doc)
            block_cursor.setPosition(block.position())

            if decrease:
                text = block.text()
                remove_chars = 0
                idx = 0
                while idx < len(text) and remove_chars < len(self.INDENT):
                    ch = text[idx]
                    if ch == " ":
                        idx += 1
                        remove_chars += 1
                    elif ch == "\t":
                        idx += 1
                        remove_chars = len(self.INDENT)
                        break
                    else:
                        break

                if idx > 0:
                    block_cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        idx,
                    )
                    block_cursor.removeSelectedText()
                    if block.blockNumber() == caret_block_number and not has_selection:
                        removed_on_caret_line = idx
            else:
                block_cursor.insertText(self.INDENT)

            if block == end_block:
                break
            block = block.next()

        cursor.endEditBlock()

        if has_selection:
            new_cursor = self.textCursor()
            new_cursor.setPosition(start_block.position())
            new_cursor.setPosition(
                end_block.position() + end_block.length() - 1,
                QTextCursor.MoveMode.KeepAnchor,
            )
            self.setTextCursor(new_cursor)
        else:
            block = doc.findBlockByNumber(caret_block_number)
            new_column = max(0, caret_column - removed_on_caret_line)
            new_pos = block.position() + new_column
            new_cursor = QTextCursor(doc)
            new_cursor.setPosition(new_pos)
            self.setTextCursor(new_cursor)

    def _add_indent_at_line_start(self):
        """Add 4 spaces at the start of the current line or selected lines."""
        cursor = self.textCursor()
        doc = self.document()

        has_selection = cursor.hasSelection()
        sel_start = cursor.selectionStart() if has_selection else cursor.position()
        sel_end = cursor.selectionEnd() if has_selection else cursor.position()

        start_block = doc.findBlock(sel_start)
        end_index = max(sel_start, sel_end - 1)
        end_block = doc.findBlock(end_index)

        caret_block_number = cursor.block().blockNumber()
        caret_column = cursor.position() - cursor.block().position()

        cursor.beginEditBlock()

        block = start_block
        while block.isValid():
            block_cursor = QTextCursor(doc)
            block_cursor.setPosition(block.position())
            block_cursor.insertText(self.INDENT)

            if block == end_block:
                break
            block = block.next()

        cursor.endEditBlock()

        if has_selection:
            new_cursor = self.textCursor()
            new_cursor.setPosition(start_block.position())
            new_cursor.setPosition(
                end_block.position() + end_block.length() - 1,
                QTextCursor.MoveMode.KeepAnchor,
            )
            self.setTextCursor(new_cursor)
        else:
            block = doc.findBlockByNumber(caret_block_number)
            new_column = caret_column + len(self.INDENT)
            new_pos = block.position() + new_column
            new_cursor = QTextCursor(doc)
            new_cursor.setPosition(new_pos)
            self.setTextCursor(new_cursor)

    def _selection_spans_multiple_blocks(self) -> bool:
        """Check if the current selection spans multiple text blocks (lines)."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        if start == end:
            return False
        doc = self.document()
        start_block = doc.findBlock(start)
        end_block = doc.findBlock(max(start, end - 1))
        return start_block != end_block


    def _insert_line_below(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()

        # Move to end of current block
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertBlock()

        current_line = cursor.block().previous().text()
        indent_match = re.match(r"\s*", current_line)
        indent = indent_match.group(0) if indent_match else ""
        cursor.insertText(indent)

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
        self.line_number_area.setFont(font)
        self.update_line_number_area_width(0)
        self.line_number_area.update()

    def _reset_font_size(self):
        font = self.font()
        font.setPointSize(self.DEFAULT_FONT_SIZE)
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.line_number_area.setFont(font)
        self.update_line_number_area_width(0)
        self.line_number_area.update()
    
    def _trigger_completion(self):
        """Trigger autocompletion at current cursor position."""
        if not self.completer.enabled:
            return
        
        cursor = self.textCursor()
        
        # Get word under cursor to filter completions
        cursor_pos = cursor.position()
        block = cursor.block()
        text = block.text()
        pos_in_block = cursor.positionInBlock()
        
        # Find start of current word
        word_start = pos_in_block
        while word_start > 0 and (text[word_start - 1].isalnum() or text[word_start - 1] == '_'):
            word_start -= 1
        
        current_word = text[word_start:pos_in_block]
        
        # Get completions from Jedi with namespace support
        source_code = self.toPlainText()
        line_num = block.blockNumber() + 1  # Jedi uses 1-based line numbers
        column = pos_in_block
        
        completions = self.completer.get_completions(
            source_code, line_num, column, self.project_file_path, 
            namespace=self.custom_namespace
        )
        
        if not completions:
            self.completion_popup.hide()
            self._completion_active = False
            return
        
        # Filter completions by current word
        if current_word:
            filtered = [
                c for c in completions 
                if c[0].lower().startswith(current_word.lower())
            ]
            completions = filtered if filtered else completions
        
        if not completions:
            self.completion_popup.hide()
            self._completion_active = False
            return
        
        # Show popup
        self.completion_popup.set_completions(completions)
        
        # Position popup below cursor
        cursor_rect = self.cursorRect()
        popup_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        
        # Adjust if popup would go off screen
        screen_geom = self.screen().availableGeometry()
        if popup_pos.y() + self.completion_popup.height() > screen_geom.bottom():
            # Show above cursor instead
            popup_pos = self.mapToGlobal(cursor_rect.topLeft())
            popup_pos.setY(popup_pos.y() - self.completion_popup.height())
        
        self.completion_popup.move(popup_pos)
        self.completion_popup.show()
        self.completion_popup.raise_()
        self._completion_active = True
    
    def _accept_completion(self):
        """Accept the currently selected completion."""
        completion = self.completion_popup.current_completion()
        if completion:
            self._insert_completion(completion)
        self.completion_popup.hide()
        self._completion_active = False
    
    def _insert_completion(self, completion_text):
        """Insert the selected completion, replacing the partial word."""
        cursor = self.textCursor()
        
        # Find and select the partial word to replace
        block = cursor.block()
        text = block.text()
        pos_in_block = cursor.positionInBlock()
        
        # Find start of current word
        word_start = pos_in_block
        while word_start > 0 and (text[word_start - 1].isalnum() or text[word_start - 1] == '_'):
            word_start -= 1
        
        # Select and replace the partial word
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, word_start)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, pos_in_block - word_start)
        cursor.insertText(completion_text)
        cursor.endEditBlock()
        
        self.setTextCursor(cursor)
        self.setFocus()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 30 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width() + 5, 0, 0, 0)

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

        # Get current selection range
        cursor = self.textCursor()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # Check if this line is part of the selection
                block_start = block.position()
                block_end = block_start + block.length()
                is_selected = (block_start < selection_end and block_end > selection_start)
                
                # Use brighter color and bold font for selected lines
                if is_selected:
                    painter.setPen(QColor("#abb2bf"))  # Brighter color
                    font = painter.font()
                    font.setWeight(QFont.Weight.Bold)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor("#5c6370"))  # Normal color
                    font = painter.font()
                    font.setWeight(QFont.Weight.Normal)
                    painter.setFont(font)
                    
                painter.drawText(0, int(top), self.line_number_area.width() - 12, self.fontMetrics().height(),
                                Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


if __name__ == "__main__":
    import os
    app = QApplication(sys.argv)
    widget = CodeEditor()

    with open(os.path.join("tests", "sample_editor_script.py"), 'r', encoding='utf-8') as f:
        new_file = f.read()
    widget.setPlainText(new_file)
    widget.resize(1280, 720)
    widget.show()
    sys.exit(app.exec())