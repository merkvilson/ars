from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QHeaderView,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
import numpy as np
from theme import StyleSheets
from theme.fonts.new_fonts import get_font
from core.sound_manager import play_sound


def create_icon(symbol, color="#E0E0E0", size=128):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    font = get_font(size=int(size*0.8), font_name="icomoon.ttf")
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
    painter.end()
    
    icon = QIcon(pixmap)
    # Add the same pixmap for Selected mode to prevent automatic tinting
    icon.addPixmap(pixmap, QIcon.Mode.Selected, QIcon.State.Off)
    icon.addPixmap(pixmap, QIcon.Mode.Selected, QIcon.State.On)
    return icon


class HierarchyTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.itemEntered.connect(self.on_item_entered)

    def on_item_entered(self, item, column):
        play_sound("hover")

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
        self.uid_to_item = {}  # Map UID to QTreeWidgetItem

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
        self.tree.setIconSize(QSize(24, 24))
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
        self.manager.parent_changed.connect(self.on_parent_changed)
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree.itemChanged.connect(self.on_item_renamed)

        self.layout.addWidget(self.tree)

        # Populate from existing objects
        self.populate_from_manager()

    def populate_from_manager(self):
        self.tree.clear()
        self.id_to_obj.clear()
        self.uid_to_item.clear()
        for i, obj in enumerate(self.manager._objects):
            uid = id(obj)
            self.id_to_obj[uid] = obj
            self.add_tree_item(i, obj, uid)

    def add_tree_item(self, index, obj, uid):
        item = QTreeWidgetItem([str(obj.name)])
        item.setIcon(0, create_icon(obj.symbol))
        item.setData(0, Qt.ItemDataRole.UserRole, uid)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.tree.insertTopLevelItem(index, item)
        self.uid_to_item[uid] = item


    def on_object_added(self, index, obj):
        uid = id(obj)
        self.id_to_obj[uid] = obj
        
        # Check if object has a parent
        parent_obj = getattr(obj, '_parent', None)
        if parent_obj:
            # Find parent's tree item
            parent_uid = id(parent_obj)
            parent_item = self.uid_to_item.get(parent_uid)
            if parent_item:
                # Add as child of parent
                item = QTreeWidgetItem([str(obj.name)])
                item.setIcon(0, create_icon(obj.symbol))
                item.setData(0, Qt.ItemDataRole.UserRole, uid)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                parent_item.addChild(item)
                parent_item.setExpanded(True)
                self.uid_to_item[uid] = item
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

    def cleanup_items_recursive(self, item):
        uid = item.data(0, Qt.ItemDataRole.UserRole)
        if uid in self.uid_to_item:
            del self.uid_to_item[uid]
        for i in range(item.childCount()):
            self.cleanup_items_recursive(item.child(i))

    def on_object_removed(self, index, obj):
        uid = id(obj)
        item = self.uid_to_item.get(uid)
        if item:
            parent_item = item.parent()
            if parent_item is None:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            else:
                parent_item.takeChild(parent_item.indexOfChild(item))
            self.cleanup_items_recursive(item)
        self.id_to_obj.pop(uid, None)

    def on_parent_changed(self, child_obj, parent_obj):
        child_uid = id(child_obj)
        child_item = self.uid_to_item.get(child_uid)
        
        if not child_item:
            return

        # Detach from current parent
        current_parent_item = child_item.parent()
        if current_parent_item:
            current_parent_item.takeChild(current_parent_item.indexOfChild(child_item))
        else:
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(child_item))

        # Attach to new parent
        if parent_obj:
            parent_uid = id(parent_obj)
            parent_item = self.uid_to_item.get(parent_uid)
            if parent_item:
                parent_item.addChild(child_item)
                parent_item.setExpanded(True)
            else:
                # Fallback: add to top level if parent not found in tree
                self.tree.addTopLevelItem(child_item)
        else:
            self.tree.addTopLevelItem(child_item)

    def on_active_changed(self, index):
        if index < 0 or index >= len(self.manager._objects):
            return
        obj = self.manager._objects[index]
        uid = id(obj)
        item = self.uid_to_item.get(uid)
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

    def get_transform_matrix(self, transform):
        if hasattr(transform, 'matrix'):
            return transform.matrix
        return np.eye(4, dtype=np.float32)

    def get_node_world_matrix(self, node):
        # Build chain from node up to scene
        chain = []
        current = node
        while current is not None and current != self.manager._view.scene:
            chain.append(current)
            current = current.parent
        
        # Calculate World = Local @ Parent @ ... @ Root (Row-Major)
        matrix = np.eye(4, dtype=np.float32)
        for n in chain:
            if hasattr(n, 'transform') and hasattr(n.transform, 'matrix'):
                matrix = matrix @ n.transform.matrix
        
        return matrix

    def get_object_world_matrix(self, obj):
        return self.get_node_world_matrix(obj.rotation_visual)

    def set_object_world_matrix(self, obj, target_matrix):
        parent_node = obj.visual.parent
        parent_matrix = self.get_node_world_matrix(parent_node)
        
        try:
            inv_parent = np.linalg.inv(parent_matrix)
        except np.linalg.LinAlgError:
            inv_parent = np.eye(4)
            
        # Local = World @ inv(Parent) (Row-Major)
        local_matrix = target_matrix @ inv_parent
        
        # Extract translation (Row 3 in Row-Major)
        translation = local_matrix[3, :3].copy()
        
        # Extract rotation/scale (remove translation)
        rs_matrix = local_matrix.copy()
        rs_matrix[3, :3] = 0.0
        rs_matrix[3, 3] = 1.0
        
        # Apply
        obj.set_position(*translation)
        obj.rotation_visual.transform.matrix = rs_matrix

    def sync_manager_order(self):
        # Capture world transforms
        world_transforms = {}
        for obj in self.manager._objects:
            world_transforms[id(obj)] = self.get_object_world_matrix(obj)

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

        # Restore transforms in top-down order to ensure parents are positioned before children
        def restore_transforms_recursive(item: QTreeWidgetItem):
            uid = item.data(0, Qt.ItemDataRole.UserRole)
            obj = self.id_to_obj.get(uid)
            if obj and id(obj) in world_transforms:
                self.set_object_world_matrix(obj, world_transforms[id(obj)])
            
            for i in range(item.childCount()):
                restore_transforms_recursive(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            restore_transforms_recursive(self.tree.topLevelItem(i))

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

        self.manager.reorder_objects(all_objs)