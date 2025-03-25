from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox
)
from database import obter_conexao


class MoveItemDialog(QDialog):
    """
    Diálogo para mover um item entre diretórios.
    """

    def __init__(self, parent=None, current_directory_id=None):
        super().__init__(parent)
        self.setWindowTitle("Mover Item")
        self.setMinimumSize(300, 400)

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        self.btn_ok = QPushButton("Mover")
        self.btn_ok.clicked.connect(self.accept)
        layout.addWidget(self.btn_ok)

        self.selected_directory_id = None
        self.load_directories(current_directory_id)

        self.tree.itemClicked.connect(self.on_item_selected)

    def load_directories(self, current_directory_id):
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, parent_id FROM directories")
                rows = cursor.fetchall()
            dirs = {row[0]: (row[1], row[2]) for row in rows}

            def add_children(parent_item, parent_id):
                for d_id, (d_name, d_parent) in dirs.items():
                    if d_parent == parent_id:
                        item = QTreeWidgetItem([d_name])
                        item.setData(0, Qt.UserRole, d_id)
                        parent_item.addChild(item)
                        add_children(item, d_id)

            root_item = self.tree.invisibleRootItem()
            for d_id, (d_name, d_parent) in dirs.items():
                if d_parent is None:
                    item = QTreeWidgetItem([d_name])
                    item.setData(0, Qt.UserRole, d_id)
                    root_item.addChild(item)
                    add_children(item, d_id)
            self.tree.expandAll()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar diretórios: {e}")

    def on_item_selected(self, item, column):
        self.selected_directory_id = item.data(0, Qt.UserRole)
