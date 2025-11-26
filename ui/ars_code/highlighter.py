import re
import keyword
import builtins
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import (
    QColor,
    QTextCharFormat,
    QSyntaxHighlighter,
    QFont,
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
        self.fmt_unused = mkfmt("#4b5263", italic=True)  # Unused variables/imports (darker grey, italic)

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
        
        # Icon characters
        self.re_icon_char = QRegularExpression("(?!)")
        try:
            from theme.fonts import font_icons, new_fonts
            # Ensure font is loaded to get family name
            f = new_fonts.get_font(10, "icomoon.ttf")
            self.icon_font_family = f.family()
            
            if hasattr(font_icons, "ICON_FULL_LIST"):
                # Build regex for all icon characters
                # Escape them just in case, though they are likely safe
                chars = "".join(re.escape(c) for c in font_icons.ICON_FULL_LIST)
                self.re_icon_char = QRegularExpression(f"[{chars}]")
                
            self.fmt_icon_char = QTextCharFormat()
            self.fmt_icon_char.setFontFamily(self.icon_font_family)
            self.fmt_icon_char.setForeground(QColor("#98c379")) 
        except ImportError:
            pass

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

    def set_unused_ranges(self, ranges):
        """
        Set the list of unused variable/import ranges.
        ranges: list of (line_idx, start_col, length)
        """
        self.unused_ranges = {}
        for line, start, length in ranges:
            if line not in self.unused_ranges:
                self.unused_ranges[line] = []
            self.unused_ranges[line].append((start, length))
        self.rehighlight()

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
        
        # 8) Icon characters
        if hasattr(self, 're_icon_char'):
            self._apply_regex(self.re_icon_char, self.fmt_icon_char, text, protected)

        # 9) Unused variables/imports
        block_num = self.currentBlock().blockNumber()
        if hasattr(self, 'unused_ranges') and block_num in self.unused_ranges:
             for start, length in self.unused_ranges[block_num]:
                 if not self._overlaps(protected, start, length):
                     self.setFormat(start, length, self.fmt_unused)

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
