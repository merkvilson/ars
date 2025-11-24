import jedi
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStyledItemDelegate,
    QStyle,
    QListWidget,
    QListWidgetItem,
)

class JediCompleter:
    """Wrapper around Jedi for Python autocompletion."""
    
    def __init__(self):
        self.enabled = True
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


class CompletionDelegate(QStyledItemDelegate):
    """Delegate for rendering completion items with color-coded icons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.type_colors = {
            'function': '#61afef',
            'method': '#61afef',
            'class': '#e5c07b',
            'module': '#c678dd',
            'instance': '#98c379',
            'keyword': '#c678dd',
            'statement': '#c678dd',
            'param': '#d19a66',
        }
        self.type_symbols = {
            'function': 'ƒ',
            'method': 'm',
            'class': 'C',
            'module': 'M',
            'instance': 'v',
            'keyword': 'K',
            'statement': 'S',
            'param': 'p',
        }
        self.padding = 5

    def paint(self, painter, option, index):
        painter.save()
        
        # Draw background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#3e4451"))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor("#2c313c"))
        else:
            painter.fillRect(option.rect, QColor("#1e2127"))

        # Get data
        name = index.data(Qt.ItemDataRole.UserRole)
        comp_type = index.data(Qt.ItemDataRole.UserRole + 1)
        signature = index.data(Qt.ItemDataRole.UserRole + 2)
        icon_char = index.data(Qt.ItemDataRole.UserRole + 3)
        
        if not name:
            painter.restore()
            return

        rect = option.rect
        
        # Draw Symbol
        original_font = painter.font()
        
        if icon_char:
            try:
                from theme.fonts import new_fonts
                # Make icon larger than text
                icon_size = max(16, original_font.pointSize() + 6)
                font = new_fonts.get_font(icon_size, "icomoon.ttf")
                painter.setFont(font)
                symbol = icon_char
                color = QColor("#e0e0e0")
            except ImportError:
                symbol = '?'
                color = QColor("#abb2bf")
                painter.setFont(original_font)
        else:
            symbol = self.type_symbols.get(comp_type, '•')
            color = QColor(self.type_colors.get(comp_type, '#abb2bf'))
            
            symbol_font = QFont(original_font)
            symbol_font.setPointSize(max(10, original_font.pointSize() + 4))
            symbol_font.setBold(True)
            painter.setFont(symbol_font)
        
        painter.setPen(color)
        # Draw symbol on the left
        symbol_width = 30
        symbol_rect = QRect(rect.left() + self.padding, rect.top(), symbol_width, rect.height())
        painter.drawText(symbol_rect, Qt.AlignmentFlag.AlignCenter, symbol)
        
        # Restore font for name
        painter.setFont(original_font)
        
        # Draw Name
        text_offset = symbol_width + self.padding + 5
        text_rect = QRect(rect.left() + text_offset, rect.top(), rect.width() - text_offset, rect.height())
        painter.setPen(QColor("#abb2bf"))
        
        # Calculate name width to position signature
        font_metrics = painter.fontMetrics()
        name_width = font_metrics.horizontalAdvance(name)
        
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
        
        # Draw Signature (if fits)
        if signature:
            painter.setPen(QColor("#5c6370")) # Dimmer color for signature
            sig_rect = QRect(text_rect.left() + name_width, text_rect.top(), text_rect.width() - name_width, text_rect.height())
            painter.drawText(sig_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, signature)

        painter.restore()
        
    def sizeHint(self, option, index):
        return QSize(200, 30)


class CompletionPopup(QWidget):
    """Popup widget displaying autocompletion suggestions."""
    
    completion_selected = pyqtSignal(str, str)  # Emitted when user selects a completion
    
    def __init__(self, parent=None):
        # Use ToolTip window type - it never steals focus!
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        
        # Critical: Don't take focus from the editor!
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.list_widget = QListWidget()
        self.list_widget.setMouseTracking(True)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setItemDelegate(CompletionDelegate(self.list_widget))
        
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
        fixed_font = QFont(font)
        fixed_font.setPointSize(14)
        self.list_widget.setFont(fixed_font)
    
    def set_completions(self, completions):
        """
        Set completion items.
        
        Args:
            completions: List of tuples (name, type, signature, [icon_char])
        """
        
        self.list_widget.clear()
        self.completions_data = completions
        
        for item_data in completions:
            name = item_data[0]
            comp_type = item_data[1]
            signature = item_data[2]
            icon_char = item_data[3] if len(item_data) > 3 else None
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setData(Qt.ItemDataRole.UserRole + 1, comp_type)
            item.setData(Qt.ItemDataRole.UserRole + 2, signature)
            if icon_char:
                item.setData(Qt.ItemDataRole.UserRole + 3, icon_char)
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
        item_height = 30 # Fixed height from delegate sizeHint
        total_height = item_height * visible_items + 4  # +4 for borders
        
        # Calculate required width based on longest item
        max_width = 0
        font_metrics = self.list_widget.fontMetrics()
        for i in range(item_count):
            item = self.list_widget.item(i)
            if item:
                name = item.data(Qt.ItemDataRole.UserRole) or ""
                signature = item.data(Qt.ItemDataRole.UserRole + 2) or ""
                # Approximate width: padding + symbol + padding + name + signature
                text_width = font_metrics.horizontalAdvance(name + signature)
                max_width = max(max_width, text_width)
        
        # Add padding for icon (40px), margins and scrollbar
        total_width = max_width + 70
        total_width = max(200, min(600, total_width))  # Min 200, max 600
        
        self.resize(total_width, total_height)
    
    def current_completion(self):
        """Get the currently selected completion text."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def current_completion_type(self):
        """Get the currently selected completion type."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole + 1)
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
        comp_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if completion:
            self.completion_selected.emit(completion, comp_type)
            self.hide()
