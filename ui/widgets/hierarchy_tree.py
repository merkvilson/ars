from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QHeaderView,
)
from PyQt6.QtCore import Qt
from theme import StyleSheets
from util_functions.colorize_png import colorize_icon


class HierarchyTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def dropEvent(self, event):
        # Preserve active object across reorder
        window = self.parent().parent()  # Fixed: Reach ObjectHierarchyWindow
        manager = window.manager
        if manager._active_idx >= 0 and manager._active_idx < len(manager._objects):
            old_active_obj = manager._objects[manager._active_idx]
        else:
            old_active_obj = None

        super().dropEvent(event)

        # Sync order after drop
        window.sync_manager_order()

        # Update active index if needed
        if old_active_obj and old_active_obj in manager._objects:
            new_idx = manager._objects.index(old_active_obj)
            manager.set_active(new_idx)


class ObjectHierarchyWindow(QWidget):
    def __init__(self, viewport, parent=None):
        super().__init__(parent)
        self.viewport = viewport
        self.manager = viewport._objectManager
        self.id_to_obj = {}  # Map UID (id(obj)) to obj for safe reference

        self.setFixedSize(200, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(StyleSheets.HIERARCHY_STYLE)

        # Container for all widgets
        self.container = QWidget(self)
        self.container.setObjectName("hierarchyWidget")
        self.container.setGeometry(0, 0, self.width(), self.height())

        self.layout = QVBoxLayout(self.container)

        # Tree widget
        self.tree = HierarchyTree(self.container)
        self.tree.setHeaderHidden(True)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree.setAnimated(True)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectItems)

        # Context menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect signals
        self.manager.object_added.connect(self.on_object_added)
        self.manager.object_removed.connect(self.on_object_removed)
        self.manager.active_changed.connect(self.on_active_changed)
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree.itemChanged.connect(self.on_item_renamed)

        self.layout.addWidget(self.tree)

        # Populate from existing objects
        self.populate_from_manager()

    def populate_from_manager(self):
        self.tree.clear()
        self.id_to_obj.clear()
        for i, obj in enumerate(self.manager._objects):
            uid = id(obj)
            self.id_to_obj[uid] = obj
            self.add_tree_item(i, obj, uid)

    def add_tree_item(self, index, obj, uid):
        item = QTreeWidgetItem([obj.name])
        item.setIcon(0, self.get_icon_for(obj))
        item.setData(0, Qt.ItemDataRole.UserRole, uid)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.tree.insertTopLevelItem(index, item)

    def get_icon_for(self, obj):
        # Placeholder: Customize based on object type
        color = "white"  # Can map to type, e.g., if isinstance(obj, CSphere): color = "orange"
        return colorize_icon(r"theme/icons/objects.png", color)

    def on_object_added(self, index, obj):
        uid = id(obj)
        self.id_to_obj[uid] = obj
        
        # Check if object has a parent
        parent_obj = getattr(obj, '_parent', None)
        if parent_obj:
            # Find parent's tree item
            parent_uid = id(parent_obj)
            parent_item, _ = self.find_item_by_uid(parent_uid)
            if parent_item:
                # Add as child of parent
                item = QTreeWidgetItem([obj.name])
                item.setIcon(0, self.get_icon_for(obj))
                item.setData(0, Qt.ItemDataRole.UserRole, uid)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                parent_item.addChild(item)
                parent_item.setExpanded(True)
                return
        
        # Add as top-level item - calculate correct position
        top_level_index = 0
        for i in range(index):
            if i < len(self.manager._objects):
                check_obj = self.manager._objects[i]
                # Only count objects without parents (top-level objects)
                if not getattr(check_obj, '_parent', None):
                    top_level_index += 1
        
        self.add_tree_item(top_level_index, obj, uid)

    def find_item_by_uid(self, uid):
        def search(parent_item=None):
            if parent_item is None:
                count = self.tree.topLevelItemCount()
                get_item = self.tree.topLevelItem
            else:
                count = parent_item.childCount()
                get_item = parent_item.child
            for i in range(count):
                item = get_item(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == uid:
                    return item, parent_item
                found_item, found_parent = search(item)
                if found_item:
                    return found_item, found_parent
            return None, None
        return search()

    def on_object_removed(self, index, obj):
        uid = id(obj)
        item, parent_item = self.find_item_by_uid(uid)
        if item:
            if parent_item is None:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            else:
                parent_item.takeChild(parent_item.indexOfChild(item))
        self.id_to_obj.pop(uid, None)

    def on_active_changed(self, index):
        if index < 0 or index >= len(self.manager._objects):
            return
        obj = self.manager._objects[index]
        uid = id(obj)
        item, _ = self.find_item_by_uid(uid)
        if item:
            self.tree.blockSignals(True)
            self.tree.clearSelection()
            item.setSelected(True)
            self.tree.scrollToItem(item)
            self.tree.blockSignals(False)

    def on_tree_selection_changed(self):
        selected = self.tree.selectedItems()
        if selected:
            uid = selected[0].data(0, Qt.ItemDataRole.UserRole)
            obj = self.id_to_obj.get(uid)
            if obj:
                index = self.manager._objects.index(obj)
                # Set selection state which triggers selection_changed signal
                self.manager.set_selection_state([index], index)

    def on_item_renamed(self, item, column):
        if column == 0:
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            obj = self.id_to_obj.get(uid)
            if obj:
                obj.name = item.text(0)

    def sync_manager_order(self):
        # Reset parents and children
        for obj in self.manager._objects:
            obj._parent = None
            obj._children = []
            obj.visual.parent = self.manager._view.scene  # Reset to root

        # Set parents based on tree structure
        def set_parents(item: QTreeWidgetItem, parent_obj=None):
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            obj = self.id_to_obj.get(uid)
            if obj:
                obj.set_parent(parent_obj)
                for i in range(item.childCount()):
                    set_parents(item.child(i), obj)

        for i in range(self.tree.topLevelItemCount()):
            set_parents(self.tree.topLevelItem(i), None)

        # Set visual parents
        for obj in self.manager._objects:
            if obj._parent is None:
                obj.visual.parent = self.manager._view.scene
            else:
                obj.visual.parent = obj._parent.visual

        # Collect all objects in depth-first order
        def collect_objs(item: QTreeWidgetItem, objs: list):
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            obj = self.id_to_obj.get(uid)
            if obj:
                objs.append(obj)
            for i in range(item.childCount()):
                collect_objs(item.child(i), objs)

        all_objs = []
        for i in range(self.tree.topLevelItemCount()):
            collect_objs(self.tree.topLevelItem(i), all_objs)

        self.manager._objects = all_objs
        self.manager._rebuild_picking()