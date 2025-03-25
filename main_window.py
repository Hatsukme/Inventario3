import csv
import json
import os
import shutil
import zipfile

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import (QAbstractItemView, QHeaderView,
                             QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
                             QTreeWidgetItem, QTableWidget, QTableWidgetItem,
                             QPushButton, QFileDialog, QLineEdit, QMessageBox, QDialog, QComboBox, QMenu, QAction,
                             QColorDialog, QCompleter, QToolButton, QStyle, QFrame, QToolTip)

from atalhos import setup_shortcuts
from config import get_config_path
from database import (
    verificar_ou_criar_db, criar_pasta_imagens, obter_conexao,
    NOME_DB, IMAGES_FOLDER, set_database_path
)
from dialogs.atalhos_dialog import atalhosDialog
from dialogs.directory_dialog import DirectoryDialog
from dialogs.item_detail_dialog import ItemDetailDialog
from dialogs.item_dialog import ItemDialog
from dialogs.notas_dialog import NoteDialog  # Nosso diálogo para notas
from dialogs.sobre_dialog import sobreDialog
from notes_utils import load_notes, save_notes, load_appdata_notes


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory")

        # Create/check DB and images folder
        verificar_ou_criar_db()
        criar_pasta_imagens()

        # Load settings (theme, window position, etc.)
        self.load_config()

        # Setup menu bar
        self.setup_menu()

        # Variables for directory search
        self.current_search_text = ""
        self.current_search_results = []
        self.current_search_index = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Search layout
        search_layout = QHBoxLayout()
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText(
            "Search by title, description, responsible or directory..."
        )
        self.search_line_edit.returnPressed.connect(self.search_items)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.search_items)

        btn_clear = QPushButton("Clear Search")
        btn_clear.clicked.connect(self.clear_search)

        search_layout.addWidget(self.search_line_edit)
        search_layout.addWidget(btn_search)
        search_layout.addWidget(btn_clear)
        main_layout.addLayout(search_layout)

        # Splitter for directory tree and items table
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Directory tree
        self.tree_directories = QtWidgets.QTreeWidget()
        self.tree_directories.setHeaderLabel("Directories")
        self.tree_directories.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_directories.customContextMenuRequested.connect(self.on_tree_context_menu)
        self.tree_directories.itemClicked.connect(self.on_directory_selected)
        self.tree_directories.header().setStretchLastSection(False)
        self.tree_directories.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_directories.setDragEnabled(True)
        self.tree_directories.viewport().setAcceptDrops(True)
        self.tree_directories.setDropIndicatorShown(True)
        self.tree_directories.setDefaultDropAction(Qt.MoveAction)
        self.tree_directories.setSelectionMode(QtWidgets.QTreeWidget.SingleSelection)
        self.tree_directories.setDragDropMode(QtWidgets.QTreeWidget.InternalMove)
        self.tree_directories.viewport().installEventFilter(self)

        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)

        # Toolbar for expanding/collapsing
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(5)

        btn_expand = QToolButton()
        btn_expand.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        btn_expand.setToolTip("Expand All")
        btn_expand.clicked.connect(self.tree_directories.expandAll)
        control_layout.addWidget(btn_expand)

        btn_collapse = QToolButton()
        btn_collapse.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        btn_collapse.setToolTip("Collapse All")
        btn_collapse.clicked.connect(self.tree_directories.collapseAll)
        control_layout.addWidget(btn_collapse)

        control_layout.addStretch()

        btn_show_notes = QToolButton()
        btn_show_notes.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
        btn_show_notes.setToolTip("Show all notes")
        btn_show_notes.clicked.connect(self.show_all_notes)
        control_layout.addWidget(btn_show_notes)

        btn_update = QToolButton()
        btn_update.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        btn_update.setToolTip("Refresh")
        btn_update.clicked.connect(self.refresh_tree_and_table)
        control_layout.addWidget(btn_update)

        tree_layout.addWidget(control_frame)

        # Directory search field
        self.dir_search_line_edit = QLineEdit()
        self.dir_search_line_edit.setPlaceholderText("Search Directory...")
        self.dir_search_line_edit.returnPressed.connect(self.search_directory)
        tree_layout.addWidget(self.dir_search_line_edit)

        tree_layout.addWidget(self.tree_directories)
        splitter.addWidget(tree_container)

        # Items table
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(6)
        self.table_items.setHorizontalHeaderLabels(["ID", "Title", "Responsible", "Quantity", "Image", "Description"])
        self.table_items.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_items.customContextMenuRequested.connect(self.on_table_context_menu)
        self.table_items.cellDoubleClicked.connect(self.on_item_double_clicked)
        self.table_items.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_items.horizontalHeader().setSectionsMovable(True)
        self.table_items.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_items.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_items.setSizeAdjustPolicy(QAbstractItemView.AdjustToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_items.viewport().installEventFilter(self)
        splitter.addWidget(self.table_items)

        header = self.table_items.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.header_context_menu)

        # Set initial splitter sizes
        splitter.setSizes([200, 600])

        # Add item button
        self.btn_add_item = QPushButton("Add Item")
        self.btn_add_item.clicked.connect(self.add_item)
        self.btn_add_item.setFixedSize(100, 25)
        self.btn_add_item.setStyleSheet("""
            QPushButton {
                background-color: green;
                color: white;
                font-size: 10px;
                padding: 1px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_item)
        main_layout.addLayout(button_layout)

        # Load tree and table settings
        self.load_tree()
        self.restore_table_config()

        # Initialize undo stack (max 5 operations)
        self.undo_stack = []
        self.max_undo = 5

        # Setup shortcuts (Ctrl+N, Ctrl+L, Ctrl+H, F5, Ctrl+Z)
        setup_shortcuts(self)

    # -------------------- Header Context Menu --------------------
    def header_context_menu(self, pos):
        header = self.table_items.horizontalHeader()
        logical_index = header.logicalIndexAt(pos)
        if logical_index < 0:
            return
        menu = QMenu(self)
        action_asc = menu.addAction("Ascending")
        action_desc = menu.addAction("Descending")
        action = menu.exec_(header.mapToGlobal(pos))
        if action == action_asc:
            self.table_items.sortItems(logical_index, Qt.AscendingOrder)
        elif action == action_desc:
            self.table_items.sortItems(logical_index, Qt.DescendingOrder)

    # -------------------- Shortcut Methods --------------------
    def show_shortcuts(self):
        dialog = atalhosDialog()
        dialog.exec_()

    def show_about(self):
        dialog = sobreDialog()
        dialog.exec_()

    def select_last_item(self):
        self.table_items.clearSelection()
        row_count = self.table_items.rowCount()
        if row_count > 0:
            self.table_items.selectRow(row_count - 1)
            self.table_items.scrollToItem(self.table_items.item(row_count - 1, 0))

    def select_first_item(self):
        self.table_items.clearSelection()
        if self.table_items.rowCount() > 0:
            self.table_items.selectRow(0)
            self.table_items.scrollToItem(self.table_items.item(0, 0))

    def undo_last_action(self):
        if not self.undo_stack:
            QMessageBox.information(self, "Undo", "No operations to undo.")
            return

        last_action = self.undo_stack.pop()
        action_type = last_action.get("type")

        if action_type == "delete":
            data = last_action.get("data")
            try:
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO items (title, responsible, quantity, description, image_path, directory_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (data['title'], data['responsible'], data['quantity'],
                          data['description'], data['image_path'], data['directory_id']))
                    conn.commit()
                QMessageBox.information(self, "Undo", "Delete undone.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error undoing delete: {e}")

        elif action_type == "insert":
            item_id = last_action.get("item_id")
            try:
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
                    conn.commit()
                QMessageBox.information(self, "Undo", "Insert undone.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error undoing insert: {e}")

        self.refresh_table()

    # -------------------- Refresh Methods --------------------
    def refresh_table(self):
        directory_id = self.get_selected_directory_id()
        if directory_id:
            self.load_items(directory_id)
        else:
            self.table_items.setRowCount(0)

    def refresh_tree_and_table(self):
        selected_directory_id = self.get_selected_directory_id()
        self.load_tree()
        if selected_directory_id:
            def find_item_by_id(item, id_val):
                if item.data(0, Qt.UserRole) == id_val:
                    return item
                for i in range(item.childCount()):
                    res = find_item_by_id(item.child(i), id_val)
                    if res:
                        return res
                return None

            root = self.tree_directories.invisibleRootItem()
            found = None
            for i in range(root.childCount()):
                found = find_item_by_id(root.child(i), selected_directory_id)
                if found:
                    break
            if found:
                self.tree_directories.setCurrentItem(found)
        self.refresh_table()

    # -------------------- Configuration Methods --------------------
    def load_config(self):
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                window_conf = config.get("window", {})
                if window_conf:
                    self.resize(window_conf.get("width", self.width()),
                                window_conf.get("height", self.height()))
                    self.move(window_conf.get("x", self.x()),
                              window_conf.get("y", self.y()))
                self.tree_colors = config.get("tree", {}).get("colors", {})
                self.expanded_ids = config.get("tree", {}).get("expanded", [])
                self.table_config = config.get("table", {})
                self.tema_atual = config.get("theme", "light")
                if self.tema_atual == "dark":
                    self.apply_dark_theme()
                else:
                    self.apply_light_theme()
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Could not load settings: {e}")

    def save_config(self):
        config = {
            "window": {
                "width": self.width(),
                "height": self.height(),
                "x": self.x(),
                "y": self.y()
            },
            "tree": {
                "expanded": self.get_expanded_items(),
                "colors": getattr(self, "tree_colors", {})
            },
            "table": {
                "column_widths": [self.table_items.horizontalHeader().sectionSize(i)
                                  for i in range(self.table_items.columnCount())],
                "column_order": [self.table_items.horizontalHeader().logicalIndex(i)
                                 for i in range(self.table_items.columnCount())]
            },
            "theme": getattr(self, "tema_atual", "light")
        }
        try:
            with open(get_config_path(), "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not save settings: {e}")

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    # -------------------- Menu Bar --------------------
    def setup_menu(self):
        menubar = self.menuBar()

        # CSV Menu
        menu_csv = menubar.addMenu("CSV")
        action_export_csv = QAction("Export DB to CSV", self)
        action_export_csv.triggered.connect(self.export_csv)
        menu_csv.addAction(action_export_csv)
        action_import_csv = QAction("Import DB from CSV", self)
        action_import_csv.triggered.connect(self.import_csv)
        menu_csv.addAction(action_import_csv)

        # Backup Menu
        menu_backup = menubar.addMenu("Backup")
        action_backup_db = QAction("Backup DB", self)
        action_backup_db.triggered.connect(self.backup_db)
        menu_backup.addAction(action_backup_db)
        action_backup_images = QAction("Backup Images", self)
        action_backup_images.triggered.connect(self.backup_images)
        menu_backup.addAction(action_backup_images)
        action_backup_configs = QAction("Backup Configs", self)
        action_backup_configs.triggered.connect(self.backup_configs)
        menu_backup.addAction(action_backup_configs)

        # Settings Menu
        menu_config = menubar.addMenu("Settings")
        action_import_config = QAction("Import Config", self)
        action_import_config.triggered.connect(self.import_config)
        menu_config.addAction(action_import_config)
        action_toggle_theme = QAction("Toggle Theme", self)
        action_toggle_theme.triggered.connect(self.toggle_theme)
        menu_config.addAction(action_toggle_theme)
        action_connect_db = QAction("Connect to another DB", self)
        action_connect_db.triggered.connect(self.select_db)
        menu_config.addAction(action_connect_db)

        # Help Menu
        menu_help = menubar.addMenu("Help")
        action_shortcuts = QAction("Shortcuts", self)
        action_shortcuts.triggered.connect(self.show_shortcuts)
        menu_help.addAction(action_shortcuts)
        action_about = QAction("About", self)
        action_about.triggered.connect(self.show_about)
        menu_help.addAction(action_about)

    def select_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select DB", "", "SQLite DB (*.db)")
        if path:
            set_database_path(path)
            criar_pasta_imagens()
            print("Selected DB:", path)
            self.load_tree()

    # -------------------- Directory Tree Methods --------------------
    def load_tree(self):
        self.tree_directories.clear()
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, parent_id FROM directories")
                rows = cursor.fetchall()
            dirs = {r[0]: (r[1], r[2]) for r in rows}

            def add_children(parent_item, parent_id):
                for d_id, (d_name, d_parent) in dirs.items():
                    if d_parent == parent_id:
                        item = QTreeWidgetItem([d_name])
                        item.setData(0, Qt.UserRole, d_id)
                        key = f"dir_{d_id}"
                        # Primeiro, tenta o JSON do DB
                        notes_db = load_notes()
                        note_text = ""
                        note_color = ""
                        if key in notes_db:
                            note_text = notes_db[key].get("text", "")
                            note_color = notes_db[key].get("color", "")
                        else:
                            # Fallback para o AppData
                            notes_appdata = load_appdata_notes()
                            if key in notes_appdata:
                                note_text = notes_appdata[key].get("text", "")
                                note_color = notes_appdata[key].get("color", "")
                        # Definir tooltip e cor usando os métodos adequados para QTreeWidgetItem:
                        if note_text:
                            item.setToolTip(0, note_text)
                        if note_color:
                            item.setBackground(0, QColor(note_color))
                        parent_item.addChild(item)
                        add_children(item, d_id)

            root_item = self.tree_directories.invisibleRootItem()
            for d_id, (d_name, d_parent) in dirs.items():
                if d_parent is None:
                    item = QTreeWidgetItem([d_name])
                    item.setData(0, Qt.UserRole, d_id)
                    key = f"dir_{d_id}"
                    notes = load_notes()
                    if key in notes:
                        note_data = notes[key]
                        item.setToolTip(0, note_data.get("text", ""))
                        if note_data.get("color"):
                            item.setBackground(0, QColor(note_data["color"]))
                    else:
                        notes_appdata = load_appdata_notes()
                        if key in notes_appdata and notes_appdata[key].get("color"):
                            color = notes_appdata[key]["color"]
                            item.setBackground(0, QColor(color))
                            item.setToolTip(0, notes_appdata[key].get("text", ""))
                    root_item.addChild(item)
                    add_children(item, d_id)

            if hasattr(self, "expanded_ids"):
                self.restore_tree_expansion(self.expanded_ids)
            self.update_dir_completer()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading directory tree: {e}")

    def on_directory_selected(self, item, column):
        directory_id = item.data(0, Qt.UserRole)
        self.load_items(directory_id)

    def get_selected_directory_id(self):
        item = self.tree_directories.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return None

    def get_expanded_items(self):
        expanded_ids = []

        def traverse(item):
            dir_id = item.data(0, Qt.UserRole)
            if item.isExpanded():
                expanded_ids.append(dir_id)
            for i in range(item.childCount()):
                traverse(item.child(i))

        root = self.tree_directories.invisibleRootItem()
        for i in range(root.childCount()):
            traverse(root.child(i))
        return expanded_ids

    def restore_tree_expansion(self, expanded_ids):
        def traverse(item):
            dir_id = item.data(0, Qt.UserRole)
            item.setExpanded(dir_id in expanded_ids)
            for i in range(item.childCount()):
                traverse(item.child(i))

        root = self.tree_directories.invisibleRootItem()
        for i in range(root.childCount()):
            traverse(root.child(i))

    def update_dir_completer(self):
        self.dir_path_map = {}
        paths = []

        def traverse(item, path):
            current_path = f"{path}/{item.text(0)}" if path else item.text(0)
            paths.append(current_path)
            self.dir_path_map[current_path] = item
            for i in range(item.childCount()):
                traverse(item.child(i), current_path)

        root = self.tree_directories.invisibleRootItem()
        for i in range(root.childCount()):
            traverse(root.child(i), "")
        completer = QCompleter(paths)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.dir_search_line_edit.setCompleter(completer)
        completer.activated.connect(self.on_dir_completer_activated)

    def on_dir_completer_activated(self, text):
        item = self.dir_path_map.get(text)
        if item:
            self.tree_directories.setCurrentItem(item)
            parent = item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()

    def search_directory(self):
        text = self.dir_search_line_edit.text().strip().lower()
        if not text:
            return
        if text != self.current_search_text or not self.current_search_results:
            self.current_search_text = text
            self.current_search_results = [path for path in self.dir_path_map if text in path.lower()]
            self.current_search_index = 0
        else:
            self.current_search_index += 1
            if self.current_search_index >= len(self.current_search_results):
                self.current_search_index = 0
        if self.current_search_results:
            match = self.current_search_results[self.current_search_index]
            self.on_dir_completer_activated(match)
        else:
            QMessageBox.information(self, "Not found", f"Directory '{text}' not found.")

    def on_tree_context_menu(self, pos: QPoint):
        item = self.tree_directories.itemAt(pos)
        menu = QMenu(self)
        if item:
            action_add_dir = QAction("Add Subdirectory", self)
            action_add_dir.triggered.connect(self.add_subdirectory)
            menu.addAction(action_add_dir)
            action_edit_dir = QAction("Edit Directory", self)
            action_edit_dir.triggered.connect(self.edit_directory)
            menu.addAction(action_edit_dir)
            action_move_dir = QAction("Move Directory", self)
            action_move_dir.triggered.connect(self.move_directory)
            menu.addAction(action_move_dir)
            action_del_dir = QAction("Delete Directory", self)
            action_del_dir.triggered.connect(self.delete_directory)
            menu.addAction(action_del_dir)
            action_view = QAction("View Items (recursive)", self)
            action_view.triggered.connect(self.view_items)
            menu.addAction(action_view)
            action_set_color = QAction("Set Color", self)
            action_set_color.triggered.connect(lambda: self.set_color(item))
            menu.addAction(action_set_color)
            key = f"dir_{item.data(0, Qt.UserRole)}"
            notes = load_notes()
            if key in notes and notes[key].get("text"):
                action_note = QAction("Delete Note", self)
                action_note.triggered.connect(lambda: self.delete_note(key, item))
            else:
                action_note = QAction("Note", self)
                action_note.triggered.connect(lambda: self.edit_note(key, item))
            menu.addAction(action_note)
        else:
            action_add_root = QAction("Add Root Directory", self)
            action_add_root.triggered.connect(self.add_root_directory)
            menu.addAction(action_add_root)
        menu.exec_(self.tree_directories.mapToGlobal(pos))

    def add_root_directory(self):
        dialog = DirectoryDialog(self, parent_directory_id=None)
        if dialog.exec_() == QDialog.Accepted:
            self.expanded_ids = self.get_expanded_items()
            self.load_tree()

    def add_subdirectory(self):
        parent_id = self.get_selected_directory_id()
        if not parent_id:
            QMessageBox.warning(self, "Warning", "Select a directory to add a subdirectory.")
            return
        dialog = DirectoryDialog(self, parent_directory_id=parent_id)
        if dialog.exec_() == QDialog.Accepted:
            self.expanded_ids = self.get_expanded_items()
            self.load_tree()

    def edit_directory(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Warning", "Select a directory to edit.")
            return
        dialog = DirectoryDialog(self, directory_id=directory_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tree()

    def move_directory(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Warning", "Select a directory to move.")
            return
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM directories WHERE id != ?", (directory_id,))
                all_dirs = cursor.fetchall()
            dlg = QDialog(self)
            dlg.setWindowTitle("Move Directory")
            layout = QVBoxLayout(dlg)
            combo = QComboBox()
            combo.addItem("Root (no parent)", None)
            for d_id, d_name in all_dirs:
                combo.addItem(d_name, d_id)
            layout.addWidget(combo)
            btn_layout = QHBoxLayout()
            layout.addLayout(btn_layout)
            btn_ok = QPushButton("OK")
            btn_ok.clicked.connect(dlg.accept)
            btn_layout.addWidget(btn_ok)
            btn_cancel = QPushButton("Cancel")
            btn_cancel.clicked.connect(dlg.reject)
            btn_layout.addWidget(btn_cancel)
            if dlg.exec_() == QDialog.Accepted:
                new_parent_id = combo.currentData()
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE directories SET parent_id = ? WHERE id = ?", (new_parent_id, directory_id))
                    conn.commit()
                self.load_tree()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error moving directory: {e}")

    def delete_directory(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Warning", "Select a directory to delete.")
            return
        resp = QMessageBox.question(self, "Confirm", "Delete this directory and all its content?")
        if resp != QMessageBox.Yes:
            return
        self.delete_directory_recursive(directory_id)
        self.load_tree()
        self.table_items.setRowCount(0)

    def delete_directory_recursive(self, directory_id):
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM directories WHERE parent_id = ?", (directory_id,))
                subdirs = cursor.fetchall()
                for sd in subdirs:
                    self.delete_directory_recursive(sd[0])
                cursor.execute("DELETE FROM items WHERE directory_id = ?", (directory_id,))
                cursor.execute("DELETE FROM directories WHERE id = ?", (directory_id,))
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting directory: {e}")

    def set_color(self, item):
        color = QColorDialog.getColor()
        if color.isValid():
            item.setBackground(0, color)
            if not hasattr(self, "tree_colors"):
                self.tree_colors = {}
            dir_id = item.data(0, Qt.UserRole)
            self.tree_colors[str(dir_id)] = color.name()

    def delete_directory_color(self, item):
        dir_id = item.data(0, Qt.UserRole)
        if hasattr(self, "tree_colors") and str(dir_id) in self.tree_colors:
            del self.tree_colors[str(dir_id)]
        item.setBackground(0, QColor())

    def view_items(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Warning", "Select a directory.")
            return
        self.load_items_recursive(directory_id)

    # -------------------- Items Methods --------------------
    def load_items(self, directory_id):
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, responsible, quantity, image_path, description
                      FROM items
                     WHERE directory_id = ?
                """, (directory_id,))
                rows = cursor.fetchall()
            self.table_items.setColumnCount(6)
            self.table_items.setHorizontalHeaderLabels(
                ["ID", "Title", "Responsible", "Quantity", "Image", "Description"]
            )
            self.table_items.setRowCount(len(rows))
            for i, row in enumerate(rows):
                item_id, title, resp, qty, image_path, desc = row
                id_item = QTableWidgetItem(str(item_id))
                self.table_items.setItem(i, 0, id_item)
                title_item = QTableWidgetItem(title)
                key = f"item_{item_id}"
                # Tenta carregar a nota para este item
                notes_db = load_notes()
                note_text = ""
                note_color = ""
                if key in notes_db:
                    note_text = notes_db[key].get("text", "")
                    note_color = notes_db[key].get("color", "")
                else:
                    notes_appdata = load_appdata_notes()
                    if key in notes_appdata:
                        note_text = notes_appdata[key].get("text", "")
                        note_color = notes_appdata[key].get("color", "")
                if note_text:
                    title_item.setToolTip(note_text)
                if note_color:
                    title_item.setBackground(QColor(note_color))
                self.table_items.setItem(i, 1, title_item)
                self.table_items.setItem(i, 2, QTableWidgetItem(resp or ""))
                from widgets.quantity_widget import QuantityWidget
                quantity = qty if qty is not None else 0
                quantity_widget = QuantityWidget(item_id, quantity)
                self.table_items.setCellWidget(i, 3, quantity_widget)
                self.table_items.setItem(i, 4, QTableWidgetItem("Yes" if image_path else "No"))
                self.table_items.setItem(i, 5, QTableWidgetItem(desc or ""))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading items: {e}")

    def load_items_recursive(self, directory_id):
        query = """
        WITH RECURSIVE subdirs(id) AS (
            SELECT id FROM directories WHERE id = ?
            UNION ALL
            SELECT d.id FROM directories d JOIN subdirs s ON d.parent_id = s.id
        )
        SELECT items.id, items.title, items.responsible, items.quantity,
               items.image_path, directories.name, items.description
          FROM items
          JOIN directories ON items.directory_id = directories.id
         WHERE items.directory_id IN (SELECT id FROM subdirs)
        """
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (directory_id,))
                rows = cursor.fetchall()
            self.table_items.setColumnCount(7)
            self.table_items.setHorizontalHeaderLabels(
                ["ID", "Title", "Responsible", "Quantity", "Image", "Description", "Directory"]
            )
            self.table_items.setRowCount(len(rows))
            for i, row in enumerate(rows):
                item_id, title, resp, qty, image_path, dir_name, desc = row
                self.table_items.setItem(i, 0, QTableWidgetItem(str(item_id)))
                self.table_items.setItem(i, 1, QTableWidgetItem(title))
                self.table_items.setItem(i, 2, QTableWidgetItem(resp or ""))
                from widgets.quantity_widget import QuantityWidget
                quantity = qty if qty is not None else 0
                quantity_widget = QuantityWidget(item_id, quantity)
                self.table_items.setCellWidget(i, 3, quantity_widget)
                self.table_items.setItem(i, 4, QTableWidgetItem("Yes" if image_path else "No"))
                self.table_items.setItem(i, 5, QTableWidgetItem(desc or ""))
                self.table_items.setItem(i, 6, QTableWidgetItem(dir_name or ""))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading items recursively: {e}")

    def add_item(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Warning", "Select a directory to add an item.")
            return
        dlg = ItemDialog(self, directory_id=directory_id)
        if dlg.exec_() == QDialog.Accepted:
            try:
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT MAX(id) FROM items")
                    new_id = cursor.fetchone()[0]
                self.undo_stack.append({"type": "insert", "item_id": new_id})
                if len(self.undo_stack) > self.max_undo:
                    self.undo_stack.pop(0)
            except Exception as e:
                print("Error registering insert for undo:", e)
            self.load_items(directory_id)
            self.table_items.scrollToBottom()

    def get_selected_item_id(self):
        row = self.table_items.currentRow()
        if row < 0:
            return None
        item_id_item = self.table_items.item(row, 0)
        if item_id_item:
            return item_id_item.text()
        return None

    def edit_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", "Select an item to edit.")
            return
        directory_id = self.get_selected_directory_id()
        dlg = ItemDialog(self, item_id=int(item_id))
        if dlg.exec_() == QDialog.Accepted:
            self.load_items(directory_id)

    def delete_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", "Select an item to delete.")
            return
        resp = QMessageBox.question(self, "Confirm", "Delete this item?")
        if resp != QMessageBox.Yes:
            return
        try:
            directory_id = self.get_selected_directory_id()
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, responsible, quantity, description, image_path, directory_id
                      FROM items
                     WHERE id = ?
                """, (item_id,))
                data = cursor.fetchone()
            if data:
                data_dict = {
                    "title": data[0],
                    "responsible": data[1],
                    "quantity": data[2],
                    "description": data[3],
                    "image_path": data[4],
                    "directory_id": data[5]
                }
                self.undo_stack.append({"type": "delete", "data": data_dict})
                if len(self.undo_stack) > self.max_undo:
                    self.undo_stack.pop(0)
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
                conn.commit()
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting item: {e}")

    def move_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", "Select an item to move.")
            return
        from dialogs.move_item_dialog import MoveItemDialog
        dlg = MoveItemDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            new_dir_id = dlg.selected_directory_id
            if new_dir_id:
                try:
                    with obter_conexao() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE items
                               SET directory_id = ?
                             WHERE id = ?
                        """, (new_dir_id, item_id))
                        conn.commit()
                    self.load_items(self.get_selected_directory_id())
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error moving item: {e}")

    def duplicate_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", "Select an item to duplicate.")
            return
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, responsible, quantity, description, image_path, directory_id
                      FROM items
                     WHERE id = ?
                """, (item_id,))
                row = cursor.fetchone()
                if row:
                    title, responsible, quantity, description, image_path, directory_id = row
                    new_title = f"Copy of {title}"
                    cursor.execute("""
                        INSERT INTO items (title, responsible, quantity, description, image_path, directory_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_title, responsible, quantity, description, image_path, directory_id))
                    conn.commit()
                    new_id = cursor.lastrowid
                    self.undo_stack.append({"type": "insert", "item_id": new_id})
                    if len(self.undo_stack) > self.max_undo:
                        self.undo_stack.pop(0)
            current_dir = self.get_selected_directory_id()
            if current_dir:
                self.load_items(current_dir)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error duplicating item: {e}")

    def on_item_double_clicked(self, row, column):
        item_id = self.get_selected_item_id()
        if item_id:
            dlg = ItemDetailDialog(self, item_id=int(item_id))
            dlg.exec_()

    def on_table_context_menu(self, pos: QPoint):
        row = self.table_items.rowAt(pos.y())
        menu = QMenu(self)
        action_add = QAction("Add Item", self)
        action_add.triggered.connect(self.add_item)
        menu.addAction(action_add)
        if row >= 0:
            action_edit = QAction("Edit Item", self)
            action_edit.triggered.connect(self.edit_item)
            menu.addAction(action_edit)
            action_del = QAction("Delete Item", self)
            action_del.triggered.connect(self.delete_item)
            menu.addAction(action_del)
            action_move = QAction("Move Item", self)
            action_move.triggered.connect(self.move_item)
            menu.addAction(action_move)
            action_duplicate = QAction("Duplicate Item", self)
            action_duplicate.triggered.connect(self.duplicate_item)
            menu.addAction(action_duplicate)
            item_id = self.table_items.item(row, 0).text()
            key = f"item_{item_id}"
            notes = load_notes()
            if key in notes and notes[key].get("text"):
                action_note = QAction("Delete Note", self)
                action_note.triggered.connect(lambda: self.delete_note(key))
            else:
                action_note = QAction("Note", self)
                action_note.triggered.connect(lambda: self.edit_note(key))
            menu.addAction(action_note)
        menu.exec_(self.table_items.mapToGlobal(pos))

    # -------------------- Items Search --------------------
    def search_items(self):
        term = self.search_line_edit.text().strip()
        if not term:
            return
        like_term = f"%{term}%"
        query = """
        WITH RECURSIVE subdirs(id) AS (
          SELECT id FROM directories WHERE name LIKE ?
          UNION ALL
          SELECT d.id FROM directories d JOIN subdirs s ON d.parent_id = s.id
        )
        SELECT items.id, items.title, items.responsible, items.quantity,
               items.image_path, directories.name, items.description
          FROM items
          JOIN directories ON items.directory_id = directories.id
         WHERE items.title LIKE ?
            OR items.description LIKE ?
            OR items.responsible LIKE ?
            OR items.directory_id IN (SELECT id FROM subdirs)
        """
        try:
            from widgets.quantity_widget import QuantityWidget
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (like_term, like_term, like_term, like_term))
                rows = cursor.fetchall()
            self.table_items.setColumnCount(7)
            self.table_items.setHorizontalHeaderLabels(
                ["ID", "Title", "Responsible", "Quantity", "Image", "Description", "Directory"]
            )
            self.table_items.setRowCount(len(rows))
            for i, row in enumerate(rows):
                item_id, title, resp, qty, image_path, dir_name, desc = row
                self.table_items.setItem(i, 0, QTableWidgetItem(str(item_id)))
                self.table_items.setItem(i, 1, QTableWidgetItem(title))
                self.table_items.setItem(i, 2, QTableWidgetItem(resp or ""))
                quantity = qty if qty is not None else 0
                quantity_widget = QuantityWidget(item_id, quantity)
                self.table_items.setCellWidget(i, 3, quantity_widget)
                self.table_items.setItem(i, 4, QTableWidgetItem("Yes" if image_path else "No"))
                self.table_items.setItem(i, 5, QTableWidgetItem(desc or ""))
                self.table_items.setItem(i, 6, QTableWidgetItem(dir_name or ""))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error searching items: {e}")

    def clear_search(self):
        self.search_line_edit.clear()
        directory_id = self.get_selected_directory_id()
        if directory_id:
            self.load_items(directory_id)
        else:
            self.table_items.setRowCount(0)

    # -------------------- CSV & Backup --------------------
    def export_csv(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Export DB to CSV", "", "CSV Files (*.csv)")
            if not path:
                return
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM directories")
                directories = cursor.fetchall()
                dir_columns = [desc[0] for desc in cursor.description]
                cursor.execute("SELECT * FROM items")
                items = cursor.fetchall()
                item_columns = [desc[0] for desc in cursor.description]
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["=== DIRECTORIES ==="])
                writer.writerow(dir_columns)
                for row in directories:
                    writer.writerow(row)
                writer.writerow([])
                writer.writerow(["=== ITEMS ==="])
                writer.writerow(item_columns)
                for row in items:
                    writer.writerow(row)
            QMessageBox.information(self, "CSV", "Export completed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exporting CSV: {e}")

    def import_csv(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
            if not path:
                return
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                content = list(reader)
            if not content:
                QMessageBox.warning(self, "CSV", "Empty CSV file.")
                return
            try:
                idx_dir = content.index(["=== DIRECTORIES ==="])
                idx_items = content.index(["=== ITEMS ==="])
            except ValueError:
                QMessageBox.warning(self, "CSV", "Invalid CSV format (missing sections).")
                return
            dir_headers = content[idx_dir + 1]
            directories = content[idx_dir + 2:idx_items]
            item_headers = content[idx_items + 1]
            items = content[idx_items + 2:]
            idx_id_dir, idx_name_dir, idx_parent_dir = 0, 1, 2
            old_dirs = {}
            for row in directories:
                if not row:
                    continue
                old_id = int(row[idx_id_dir])
                name = row[idx_name_dir]
                parent_str = row[idx_parent_dir].strip() if len(row) > idx_parent_dir else ""
                parent_id = None if parent_str == "" else int(parent_str)
                old_dirs[old_id] = (name, parent_id)
            id_map = {}

            def insert_dir(od_id, cursor):
                if od_id in id_map:
                    return id_map[od_id]
                nm, pid = old_dirs[od_id]
                new_parent = None if pid is None or pid not in old_dirs else insert_dir(pid, cursor)
                cursor.execute("INSERT INTO directories (name, parent_id) VALUES (?, ?)", (nm, new_parent))
                new_id = cursor.lastrowid
                id_map[od_id] = new_id
                return new_id

            with obter_conexao() as conn:
                cursor = conn.cursor()
                for od_id in old_dirs:
                    insert_dir(od_id, cursor)
                conn.commit()
            idx_id_item, idx_title_item, idx_resp_item, idx_qty_item, idx_desc_item, idx_img_item, idx_dir_item = 0, 1, 2, 3, 4, 5, 6
            with obter_conexao() as conn:
                cursor = conn.cursor()
                for row in items:
                    if not row:
                        continue
                    title = row[idx_title_item]
                    responsible = row[idx_resp_item]
                    qty_str = row[idx_qty_item].strip()
                    quantity = int(qty_str) if qty_str else None
                    description = row[idx_desc_item]
                    image_path = row[idx_img_item]
                    old_dir_str = row[idx_dir_item].strip()
                    old_dir = None if old_dir_str == "" else int(old_dir_str)
                    new_dir = id_map.get(old_dir) if old_dir else None
                    cursor.execute("""
                            INSERT INTO items (title, responsible, quantity, description, image_path, directory_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (title, responsible, quantity, description, image_path, new_dir))
                conn.commit()
            QMessageBox.information(self, "CSV", "Import completed successfully.")
            self.load_tree()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importing CSV: {e}")

    def backup_db(self):
        try:
            zip_name = f"backup_db_{os.path.splitext(os.path.basename(NOME_DB))[0]}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(NOME_DB, os.path.basename(NOME_DB))
            QMessageBox.information(self, "Backup", f"DB backup created: {zip_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error backing up DB: {e}")

    def backup_images(self):
        try:
            zip_name = f"backup_images_{os.path.basename(IMAGES_FOLDER)}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(IMAGES_FOLDER):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, os.path.dirname(IMAGES_FOLDER))
                        zipf.write(full_path, arcname)
            QMessageBox.information(self, "Backup", f"Images backup created: {zip_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error backing up images: {e}")

    def backup_configs(self):
        try:
            import datetime
            config_path = get_config_path()
            folder = os.path.dirname(config_path)
            zip_name = os.path.join(folder,
                                    f"backup_configs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(config_path, os.path.basename(config_path))
            QMessageBox.information(self, "Backup", f"Configs backup created: {zip_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error backing up configs: {e}")

    def import_config(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Select Config", "", "JSON Files (*.json)")
            if not path:
                return
            destino = get_config_path()
            shutil.copy(path, destino)
            QMessageBox.information(self, "Config", "Config imported successfully. Restart the application.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importing config: {e}")

    # -------------------- Theme --------------------
    def toggle_theme(self):
        if getattr(self, "tema_atual", "light") == "light":
            self.tema_atual = "dark"
            self.apply_dark_theme()
        else:
            self.tema_atual = "light"
            self.apply_light_theme()
        self.save_theme_config()

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(0, 255, 255, 128))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QtWidgets.QApplication.instance().setPalette(palette)
        QtWidgets.QApplication.instance().setStyleSheet("""
                QToolTip {
                    color: #ffffff;
                    background-color: #2a82da;
                    border: 1px solid white;
                }
            """)
        self.setStyleSheet("QMainWindow { border: 2px solid rgba(0,255,255,0.5); }")

    def apply_light_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(225, 225, 225))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(200, 200, 200))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.Highlight, QColor(100, 100, 100))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        QtWidgets.QApplication.instance().setPalette(palette)
        QtWidgets.QApplication.instance().setStyleSheet("")
        self.setStyleSheet("QMainWindow { border: 2px solid darkgray; }")

    def save_theme_config(self):
        config_path = get_config_path()
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
            except:
                pass
        config["theme"] = self.tema_atual
        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not save theme: {e}")

    # -------------------- Restore Table Config --------------------
    def restore_table_config(self):
        if hasattr(self, "table_config") and self.table_config:
            widths = self.table_config.get("column_widths", [])
            for i, width in enumerate(widths):
                self.table_items.setColumnWidth(i, width)
            order = self.table_config.get("column_order", [])
            header = self.table_items.horizontalHeader()
            for desired_visual, logical in enumerate(order):
                current_visual = header.visualIndex(logical)
                if current_visual != desired_visual:
                    header.moveSection(current_visual, desired_visual)

    def edit_note(self, key, widget=None):
        """
        Opens the NoteDialog to add/edit a note.
        'key' should be "dir_<id>" for directories or "item_<id>" for items.
        If widget is provided, update its tooltip and background.
        """
        notes_db = load_notes()
        current_note = notes_db.get(key, {}).get("text", "")
        current_color = notes_db.get(key, {}).get("color", "")
        # Fallback para AppData
        if not current_note or not current_color:
            notes_appdata = load_appdata_notes()
            current_note = current_note or notes_appdata.get(key, {}).get("text", "")
            current_color = current_color or notes_appdata.get(key, {}).get("color", "")
        dialog = NoteDialog(current_note, current_color)
        if dialog.exec_() == QDialog.Accepted:
            note_text, note_color = dialog.get_note_data()
            notes_db[key] = {"text": note_text, "color": note_color}
            save_notes(notes_db)
            if widget is not None:
                # Verifica se o widget é um QTreeWidgetItem ou QTableWidgetItem
                from PyQt5.QtWidgets import QTreeWidgetItem, QTableWidgetItem
                if isinstance(widget, QTreeWidgetItem):
                    widget.setToolTip(0, note_text)
                    if note_color:
                        widget.setBackground(0, QColor(note_color))
                    else:
                        widget.setBackground(0, QColor())
                elif isinstance(widget, QTableWidgetItem):
                    widget.setToolTip(note_text)
                    if note_color:
                        widget.setBackground(QColor(note_color))
                    else:
                        widget.setBackground(QColor())
        self.refresh_tree_and_table()

    def delete_note(self, key, widget=None):
        """
        Deletes the note for 'key' from the DB JSON.
        Updates the widget (clearing tooltip and background) if provided.
        """
        notes_db = load_notes()
        if key in notes_db:
            del notes_db[key]
            save_notes(notes_db)
        else:
            notes_appdata = load_appdata_notes()
            if key in notes_appdata:
                del notes_appdata[key]
        if widget is not None:
            from PyQt5.QtWidgets import QTreeWidgetItem, QTableWidgetItem
            if isinstance(widget, QTreeWidgetItem):
                widget.setToolTip(0, "")
                widget.setBackground(0, QColor())
            elif isinstance(widget, QTableWidgetItem):
                widget.setToolTip("")
                widget.setBackground(QColor())
        self.refresh_tree_and_table()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            if obj == self.tree_directories.viewport():
                pos = event.pos()
                item = self.tree_directories.itemAt(pos)
                if item:
                    note_text = item.toolTip(0)
                    if note_text:
                        QToolTip.showText(event.globalPos(), note_text, self.tree_directories)
                        return True
            elif obj == self.table_items.viewport():
                pos = event.pos()
                index = self.table_items.indexAt(pos)
                if index.isValid():
                    # Vamos supor que o tooltip esteja na coluna 1
                    item = self.table_items.item(index.row(), 1)
                    if item:
                        note_text = item.toolTip()
                        if note_text:
                            QToolTip.showText(event.globalPos(), note_text, self.table_items)
                            return True
        return super().eventFilter(obj, event)

    def show_all_notes(self):
        from dialogs.notes_list_dialog import NotesListDialog
        notes = load_notes()  # Você pode querer mesclar com appdata se necessário
        dialog = NotesListDialog(notes)
        dialog.exec_()
        # Após fechar o diálogo, recarregue a árvore e a tabela para atualizar eventuais mudanças
        self.refresh_tree_and_table()
