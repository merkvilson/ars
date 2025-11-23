import re
from PyQt6.QtCore import Qt, QSize, QPoint, QEvent, QTimer, QRect
from PyQt6.QtGui import (
    QColor,
    QFont,
    QTextCursor,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import QWidget, QApplication, QPlainTextEdit
from ars_cmds.core_cmds.run_ext import run_string_code

from .highlighter import PythonHighlighter
from .completer import JediCompleter, CompletionPopup

class LineNumberArea(QWidget):
    """Line number display widget for CodeEditor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)
        
    def mousePressEvent(self, event):
        self.editor.line_number_area_mouse_press_event(event)


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
        self.multi_cursors = []
        
        # Initialize icon mappings
        self.ICON_TO_NAME = {}
        self.NAME_TO_ICON = {}
        self._is_replacing = False
        try:
            from theme.fonts import font_icons
            for name in dir(font_icons):
                if name.startswith("ICON_") and name != "ICON_FULL_LIST":
                    val = getattr(font_icons, name)
                    if isinstance(val, str):
                        # Map both with and without 'ic.' prefix
                        self.NAME_TO_ICON[name] = val
                        self.NAME_TO_ICON["ic." + name] = val
                        # Reverse map prefers 'ic.' prefix
                        self.ICON_TO_NAME[val] = "ic." + name
        except ImportError:
            pass

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

        # Ensure trailing newline on change
        self.textChanged.connect(self._ensure_trailing_newline)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setStyleSheet(
            "QPlainTextEdit {"
            f"background-color: rgba(40, 44, 52, 0.85);"
            "color: #abb2bf;"
            "border: none;"
            "border-radius: 20px;"
            "selection-color: #ffffff;"
            "selection-background-color: #3e4451;"
            "}"
        )
        
        # Install event filter on viewport to catch mouse events reliably
        self.viewport().installEventFilter(self)
        
        # Multi-cursor blinking
        self._cursor_blink_timer = QTimer(self)
        self._cursor_blink_timer.setInterval(500)
        self._cursor_blink_timer.timeout.connect(self._toggle_cursor_blink)
        self._cursor_visible = True

    def _toggle_cursor_blink(self):
        self._cursor_visible = not self._cursor_visible
        self.viewport().update()

    def _update_multi_cursor_state(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            if not self._cursor_blink_timer.isActive():
                self._cursor_blink_timer.start()
                self._cursor_visible = True
                self.setCursorWidth(0) # Hide system cursor
        else:
            if self._cursor_blink_timer.isActive():
                self._cursor_blink_timer.stop()
            self.setCursorWidth(1) # Restore system cursor
            self._cursor_visible = True # Ensure visible when reverting
            self.viewport().update()

    def eventFilter(self, obj, event):
        if obj == self.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            
            if (event.modifiers() & Qt.KeyboardModifier.AltModifier and event.button() == Qt.MouseButton.LeftButton) or \
               (event.button() == Qt.MouseButton.MiddleButton):
                
                self.setFocus()
                
                # Map viewport pos to cursor
                cursor = self.cursorForPosition(event.pos())
                main_cursor = self.textCursor()
                
                if not hasattr(self, 'multi_cursors'):
                    self.multi_cursors = []
                
                if cursor.position() != main_cursor.position():
                    found_idx = -1
                    for i, c in enumerate(self.multi_cursors):
                        if c.position() == cursor.position():
                            found_idx = i
                            break
                    
                    if found_idx != -1:
                        self.multi_cursors.pop(found_idx)
                    else:
                        self.multi_cursors.append(cursor)
                    
                    self._update_multi_cursor_state()
                    self.viewport().update()
                
                return True # Consume event
            
            if event.button() == Qt.MouseButton.LeftButton:
                if hasattr(self, 'multi_cursors') and self.multi_cursors:
                    self.multi_cursors.clear()
                    self._update_multi_cursor_state()
                    self.viewport().update()
                    # Don't return True, let default handler process the click (move cursor)
        
        return super().eventFilter(obj, event)

    def set_alpha(self, alpha: float):
        """Set the alpha (transparency) value. Alpha should be a value 0-1."""
        self.setStyleSheet(
            "QPlainTextEdit {"
            f"background-color: rgba(40, 44, 52, {alpha});"
            "color: #abb2bf;"
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

    def text_to_icons(self, text):
        """Convert text representation of icons to actual characters."""
        if not self.NAME_TO_ICON:
            return text
            
        pattern = r"\b(?:ic\.)?ICON_[A-Z0-9_]+\b"
        
        def replace_match(match):
            word = match.group(0)
            return self.NAME_TO_ICON.get(word, word)
            
        return re.sub(pattern, replace_match, text)

    def icons_to_text(self, text):
        """Convert icon characters back to text representation."""
        if not self.ICON_TO_NAME:
            return text
            
        chars = "".join(re.escape(c) for c in self.ICON_TO_NAME.keys())
        if not chars:
            return text
            
        pattern = f"[{chars}]"
        
        def replace_match(match):
            char = match.group(0)
            return self.ICON_TO_NAME.get(char, char)
            
        return re.sub(pattern, replace_match, text)

    def setPlainText(self, text):
        """Override to convert text to icons on load."""
        converted = self.text_to_icons(text)
        super().setPlainText(converted)
        
    def get_clean_code(self):
        """Get code with icons converted back to text."""
        text = self.toPlainText()
        return self.icons_to_text(text)

    def run_code(self, namespace_injection=None):
        if namespace_injection is None: namespace_injection = self.custom_namespace
        # Use get_clean_code() instead of toPlainText()
        code = self.get_clean_code()
        run_string_code(code, namespace_injection)

    def set_font_size(self, size: int):
        size = int(size)
        font = self.font()
        new_size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, size))
        font.setPointSize(new_size)
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.line_number_area.setFont(font)
        self.update_line_number_area_width(0)
        self.line_number_area.update()

    def get_font_size(self) -> int:
        return self.font().pointSize()

    def save_script(self):
        # Use get_clean_code() instead of toPlainText()
        with open(self.project_file_path, 'w', encoding='utf-8') as f:
            f.write(self.get_clean_code())

    def mousePressEvent(self, event):
        # Default handler is sufficient if eventFilter catches the special cases
        # But we keep this for debugging or fallback
        # print(f"DEBUG: mousePressEvent called. Button: {event.button()}")
        super().mousePressEvent(event)

    def viewportEvent(self, event):
        result = super().viewportEvent(event)
        if event.type() == QEvent.Type.Paint:
            self._paint_multi_cursors()
        return result

    def _paint_multi_cursors(self):
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            if not self._cursor_visible:
                return

            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor("#ffffff"), 2))
            
            offset = self.contentOffset()
            offset_point = QPoint(int(offset.x()), int(offset.y()))
            
            # Draw extra cursors AND main cursor
            cursors_to_draw = self.multi_cursors + [self.textCursor()]
            
            for c in cursors_to_draw:
                rect = self.cursorRect(c)
                # cursorRect returns content coordinates.
                # We must translate by contentOffset to get viewport coordinates.
                rect.translate(offset_point)
                
                # Ensure visible width
                rect.setWidth(2)
                
                painter.drawLine(rect.topLeft(), rect.bottomLeft())
            painter.end()

    def keyPressEvent(self, event):
        # Reset blink timer on key press
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            self._cursor_visible = True
            self._cursor_blink_timer.start()
            self.viewport().update()

        key = event.key()
        text = event.text()
        modifiers = event.modifiers()

        # Handle multi-cursor typing/deletion/navigation
        if hasattr(self, 'multi_cursors') and self.multi_cursors:
            # Check for supported keys
            is_typing = text and (text.isprintable() or text == '\t') and not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier))
            is_backspace = key == Qt.Key.Key_Backspace
            is_delete = key == Qt.Key.Key_Delete
            is_enter = key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            is_arrow = key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down)
            is_paste = (key == Qt.Key.Key_V and modifiers & Qt.KeyboardModifier.ControlModifier)
            
            if is_typing or is_backspace or is_delete or is_enter or is_arrow or is_paste:
                # Collect all cursors
                cursors = [self.textCursor()] + self.multi_cursors
                # Sort descending
                cursors.sort(key=lambda c: c.position(), reverse=True)
                
                self.textCursor().beginEditBlock()
                
                new_cursors = []
                
                # Pre-fetch clipboard text for paste
                paste_text = ""
                if is_paste:
                    paste_text = QApplication.clipboard().text()

                for c in cursors:
                    self.setTextCursor(c)
                    
                    # Perform action
                    if is_arrow:
                        mode = QTextCursor.MoveMode.KeepAnchor if (modifiers & Qt.KeyboardModifier.ShiftModifier) else QTextCursor.MoveMode.MoveAnchor
                        op = QTextCursor.MoveOperation.NoMove
                        if key == Qt.Key.Key_Left: op = QTextCursor.MoveOperation.Left
                        elif key == Qt.Key.Key_Right: op = QTextCursor.MoveOperation.Right
                        elif key == Qt.Key.Key_Up: op = QTextCursor.MoveOperation.Up
                        elif key == Qt.Key.Key_Down: op = QTextCursor.MoveOperation.Down
                        
                        self.moveCursor(op, mode)
                        
                    elif is_backspace:
                        if not self._handle_smart_backspace():
                            self.textCursor().deletePreviousChar()
                            
                    elif is_delete:
                        self.textCursor().deleteChar()
                        
                    elif is_enter:
                        self._handle_newline()
                    
                    elif is_paste:
                        if paste_text:
                            self.insertPlainText(paste_text)
                        
                    elif is_typing:
                        # Handle pair chars
                        if not self._handle_pair_chars(text, modifiers):
                            self.insertPlainText(text)
                            
                    new_cursors.append(self.textCursor())
                
                self.textCursor().endEditBlock()
                
                # Restore cursors
                # new_cursors is sorted descending (bottom to top).
                # So new_cursors[-1] is the top-most.
                
                self.setTextCursor(new_cursors[-1])
                self.multi_cursors = new_cursors[:-1]
                
                self.viewport().update()
                event.accept()
                return
            
            # If unsupported key, clear multi cursors?
            if key == Qt.Key.Key_Escape:
                self.multi_cursors.clear()
                self._update_multi_cursor_state()
                self.viewport().update()
                event.accept()
                return

        
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

        if modifiers & Qt.KeyboardModifier.AltModifier:
            if key == Qt.Key.Key_Up:
                self._move_lines_up()
                event.accept()
                return
            if key == Qt.Key.Key_Down:
                self._move_lines_down()
                event.accept()
                return

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

        if key == Qt.Key.Key_I and modifiers & Qt.KeyboardModifier.AltModifier:
            self._show_icon_picker()
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
        
        # Check for icon replacement
        if text and not self._is_replacing:
             self._check_icon_replacement()
        
        # After handling the key, manage completion popup
        if text and (text.isalnum() or text in ('_', '.')):
            # Continue showing/updating completions for valid identifier characters
            self._trigger_completion()
        elif text == ' ':
             # Trigger on space to support "from x " -> "import" and "import " -> members
             self._trigger_completion()
        elif text == ',':
             # Trigger on comma to support "import x," -> members
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

    def _move_lines_up(self):
        cursor = self.textCursor()
        doc = self.document()

        if cursor.hasSelection():
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
        else:
            start_pos = cursor.position()
            end_pos = cursor.position()

        start_block = doc.findBlock(start_pos)
        end_block = doc.findBlock(end_pos)
        
        if end_pos > start_pos and end_block.position() == end_pos:
            end_block = end_block.previous()

        if start_block.blockNumber() == 0:
            return

        prev_block = start_block.previous()
        
        cursor.beginEditBlock()
        
        prev_start = prev_block.position()
        prev_end = start_block.position()
        
        move_cursor = QTextCursor(doc)
        move_cursor.setPosition(prev_start)
        move_cursor.setPosition(prev_end, QTextCursor.MoveMode.KeepAnchor)
        text = move_cursor.selectedText() # Includes newline if not last, but prev is never last
        
        move_cursor.removeSelectedText()
        
        # If end_block was the last block, it might not have a newline.
        # We are appending 'text' (which ends in \n) to end_block.
        # If end_block has no newline, we get "ContentPrev\n". We want "Content\nPrev".
        # So we need to insert a newline before 'text', and remove the newline from 'text'?
        
        if end_block.blockNumber() == doc.blockCount() - 1:
            # We are moving something to the end.
            # 'text' is "Prev\n".
            # We want to insert "\nPrev".
            # So we strip the last char from text, and prepend \n.
            if text.endswith("\u2029") or text.endswith("\n"):
                 text = "\n" + text[:-1]
            else:
                 # Should not happen for prev_block unless it was somehow last, which it isn't
                 text = "\n" + text
        
        insert_pos = end_block.position() + end_block.length();
        
        move_cursor.setPosition(insert_pos);
        move_cursor.insertText(text);
        
        cursor.endEditBlock();
        
        shift = len(text);
        # If we changed the text structure (added \n at start), the shift logic might be tricky.
        # But wait, we removed "Prev\n" (len L) and inserted "\nPrev" (len L). Length is same.
        
        new_cursor = self.textCursor();
        new_cursor.setPosition(start_pos - shift);
        if end_pos > start_pos:
            new_cursor.setPosition(end_pos - shift, QTextCursor.MoveMode.KeepAnchor);
        self.setTextCursor(new_cursor);

    def _move_lines_down(self):
        cursor = self.textCursor()
        doc = self.document()

        if cursor.hasSelection():
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
        else:
            start_pos = cursor.position()
            end_pos = cursor.position()

        start_block = doc.findBlock(start_pos)
        end_block = doc.findBlock(end_pos)
        
        if end_pos > start_pos and end_block.position() == end_pos:
            end_block = end_block.previous()

        if end_block.blockNumber() == doc.blockCount() - 1:
            return

        next_block = end_block.next()
        
        cursor.beginEditBlock()
        
        next_start = next_block.position()
        if next_block.next().isValid():
            # Normal case: B is not last.
            next_end = next_block.next().position()
            move_cursor = QTextCursor(doc)
            move_cursor.setPosition(next_start)
            move_cursor.setPosition(next_end, QTextCursor.MoveMode.KeepAnchor)
            text = move_cursor.selectedText()
            move_cursor.removeSelectedText()
            
            insert_pos = start_block.position()
            move_cursor.setPosition(insert_pos)
            move_cursor.insertText(text)
            
            shift = len(text)
        else:
            # Special case: B is last.
            # We move B (last) to before A. A becomes last.
            move_cursor = QTextCursor(doc)
            move_cursor.setPosition(next_start)
            move_cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            text = move_cursor.selectedText() # "ContentB" (no newline)
            move_cursor.removeSelectedText()
            
            # Now we must remove the newline after A (which is now at the end of doc)
            # The newline is at end_block.position() + end_block.length()
            # But since we removed B, the doc ends at that newline.
            
            # We need to be careful with positions since we just modified the doc.
            # start_block and end_block are still valid objects but their positions might have updated?
            # No, we removed text *after* them, so their positions are unchanged.
            
            # The newline to remove is at the end of the current selection range.
            newline_pos = end_block.position() + end_block.length()
            
            delete_cursor = QTextCursor(doc)
            delete_cursor.setPosition(newline_pos)
            delete_cursor.deleteChar() # Remove \n
            
            # Insert "ContentB\n" before A
            text = text + "\n"
            insert_pos = start_block.position()
            move_cursor.setPosition(insert_pos)
            move_cursor.insertText(text)
            
            shift = len(text)

        cursor.endEditBlock()
        
        new_cursor = self.textCursor()
        new_cursor.setPosition(start_pos + shift)
        if end_pos > start_pos:
            new_cursor.setPosition(end_pos + shift, QTextCursor.MoveMode.KeepAnchor)
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


    def _ensure_trailing_newline(self):
        """Ensure the document always ends with an empty line."""
        doc = self.document()
        if doc.isEmpty():
            return
            
        last_block = doc.lastBlock()
        # If the last block contains text, we need to append a new block.
        if len(last_block.text()) > 0:
            # Save current cursor state
            current_cursor = self.textCursor()
            original_position = current_cursor.position()
            original_anchor = current_cursor.anchor()
            
            # Block signals to prevent recursion
            was_blocked = self.blockSignals(True)
            
            try:
                cursor = QTextCursor(doc)
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertBlock()
                
                # Restore cursor position explicitly
                restored_cursor = self.textCursor()
                restored_cursor.setPosition(original_anchor)
                restored_cursor.setPosition(original_position, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(restored_cursor)
                
            finally:
                self.blockSignals(was_blocked)

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
    
    def _get_icon_completions(self, filter_text):
        try:
            from theme.fonts import font_icons
        except ImportError:
            return []
            
        results = []
        for name in dir(font_icons):
            if name.startswith("ICON_") and name != "ICON_FULL_LIST":
                if filter_text and not name.lower().startswith(filter_text.lower()):
                    continue
                
                val = getattr(font_icons, name)
                if isinstance(val, str):
                    # (name, type, signature, icon_char)
                    results.append((name, 'icon', '', val))
        
        return sorted(results, key=lambda x: x[0])

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
        
        # Check for custom triggers
        # Look at text before word_start
        prefix_text = text[:word_start].rstrip()
        
        completions = []
        
        if prefix_text.endswith("ic.") or prefix_text.endswith("font_icons."):
            completions = self._get_icon_completions(current_word)
        
        if not completions:
            # Optimization: If current_word is empty (e.g. after space/comma),
            # only trigger Jedi in specific contexts to avoid performance hit on every space
            should_trigger = True
            if not current_word:
                line_text = text[:pos_in_block]
                # Check for "from ... " (expecting import)
                # Check for "from ...import ... " (expecting members)
                # Check for "import ... " (expecting modules)
                # Check for comma in import statement
                is_import_ctx = re.match(r"^\s*(from|import)\b", line_text)
                if not is_import_ctx:
                    should_trigger = False
            
            if should_trigger:
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
        comp_type = self.completion_popup.current_completion_type()
        if completion:
            self._insert_completion(completion, comp_type)
        self.completion_popup.hide()
        self._completion_active = False
    
    def _insert_completion(self, completion_text, comp_type=None):
        """Insert the selected completion, replacing the partial word."""
        # Check if it's an icon name and replace with char
        if completion_text in self.NAME_TO_ICON:
            completion_text = self.NAME_TO_ICON[completion_text]
        elif "ic." + completion_text in self.NAME_TO_ICON:
             completion_text = self.NAME_TO_ICON["ic." + completion_text]

        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        if cursor.hasSelection():
            cursor.insertText(completion_text)
        else:
            # Find and select the partial word to replace
            block = cursor.block()
            text = block.text()
            pos_in_block = cursor.positionInBlock()
            
            # Find start of current word
            word_start = pos_in_block
            while word_start > 0 and (text[word_start - 1].isalnum() or text[word_start - 1] == '_'):
                word_start -= 1
                
            # Check if preceded by "ic." or "font_icons." and include it in replacement
            if word_start >= 3 and text[word_start-3:word_start] == "ic.":
                word_start -= 3
            elif word_start >= 11 and text[word_start-11:word_start] == "font_icons.":
                word_start -= 11
            
            # Select and replace the partial word
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, word_start)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, pos_in_block - word_start)
            
            # Add space if inserting directly after comma
            if word_start > 0 and text[word_start - 1] == ',':
                completion_text = " " + completion_text
                
            cursor.insertText(completion_text)
        
        # Add parentheses for functions/methods if not in import
        if comp_type in ('function', 'method'):
            block_text = cursor.block().text().lstrip()
            if not (block_text.startswith('import ') or block_text.startswith('from ')):
                cursor.insertText("()")
                cursor.movePosition(QTextCursor.MoveOperation.Left)
            
        cursor.endEditBlock()
        
        self.setTextCursor(cursor)
        self.setFocus()

    def _check_icon_replacement(self):
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        pos = cursor.positionInBlock()
        
        # Look for pattern ending at cursor
        text_before = text[:pos]
        # Match (ic.)?ICON_...
        match = re.search(r"(?:ic\.)?ICON_[A-Z0-9_]+$", text_before)
        if match:
            word = match.group(0)
            if word in self.NAME_TO_ICON:
                self._is_replacing = True
                cursor.beginEditBlock()
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(word))
                cursor.insertText(self.NAME_TO_ICON[word])
                cursor.endEditBlock()
                self.setTextCursor(cursor)
                self._is_replacing = False

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
        
        # Try to load font/icons for painting
        try:
            from theme.fonts import font_icons, new_fonts
            icon_font = new_fonts.get_font(14, "icomoon.ttf")
            has_icons = True
        except ImportError:
            has_icons = False

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
                    
                # Draw line number
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(),
                                Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def line_number_area_mouse_press_event(self, event):
        pass

    def _show_icon_picker(self):
        completions = self._get_icon_completions("")
        if not completions:
            return
            
        self.completion_popup.set_completions(completions)
        
        # Position popup
        cursor_rect = self.cursorRect()
        popup_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        
        screen_geom = self.screen().availableGeometry()
        if popup_pos.y() + self.completion_popup.height() > screen_geom.bottom():
            popup_pos = self.mapToGlobal(cursor_rect.topLeft())
            popup_pos.setY(popup_pos.y() - self.completion_popup.height())
        
        self.completion_popup.move(popup_pos)
        self.completion_popup.show()
        self.completion_popup.raise_()
        self._completion_active = True

    def paintEvent(self, event):
        super().paintEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if (event.modifiers() & Qt.KeyboardModifier.AltModifier and event.button() == Qt.MouseButton.LeftButton) or \
           (event.button() == Qt.MouseButton.MiddleButton):
            
            new_cursor = self.cursorForPosition(event.pos())
            main_cursor = self.textCursor()
            
            if new_cursor.position() != main_cursor.position():
                # Check for overlap with existing extra cursors
                found_idx = -1
                for i, c in enumerate(self.multi_cursors):
                    if c.position() == new_cursor.position():
                        found_idx = i
                        break
                
                if found_idx != -1:
                    self.multi_cursors.pop(found_idx)
                else:
                    self.multi_cursors.append(new_cursor)
                
                self.viewport().update()
            
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.multi_cursors.clear()
            self.viewport().update()
            
        super().mousePressEvent(event)
