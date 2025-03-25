from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from database import obter_conexao
from notes_utils import load_warnings_config, save_warnings_config, get_directory_paths


class NotesListDialog(QDialog):
    def __init__(self, notes):
        super().__init__()
        self.setWindowTitle("All Notes")
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Type", "Key", "Path", "Note"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.table)

        self.populate_table(notes)
        self.load_config()

    def populate_table(self, notes):
        dir_paths = get_directory_paths()
        items = []
        # As keys devem estar no formato "dir_X" para diretórios ou "item_X" para itens.
        for key, value in notes.items():
            note_text = value.get("text", "")
            if key.startswith("dir_"):
                type_str = "Directory"
                try:
                    dir_id = int(key.split("_")[1])
                except Exception:
                    dir_id = None
                path = dir_paths.get(dir_id, "Unknown") if dir_id is not None else "Unknown"
                items.append((type_str, key, path, note_text))
            elif key.startswith("item_"):
                type_str = "Item"
                try:
                    item_id = int(key.split("_")[1])
                except Exception:
                    item_id = None
                directory_id = None
                if item_id is not None:
                    with obter_conexao() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT directory_id FROM items WHERE id = ?", (item_id,))
                        res = cursor.fetchone()
                        if res:
                            directory_id = res[0]
                path = dir_paths.get(directory_id, "Unknown") if directory_id is not None else "Unknown"
                items.append((type_str, key, path, note_text))
        self.table.setRowCount(len(items))
        for i, (type_str, key, path, note_text) in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(type_str))
            self.table.setItem(i, 1, QTableWidgetItem(key))
            self.table.setItem(i, 2, QTableWidgetItem(path))
            self.table.setItem(i, 3, QTableWidgetItem(note_text))

    def load_config(self):
        """
        Carrega a configuração do diálogo (tamanho/posição e configurações das colunas)
        a partir do arquivo de configuração do AppData, usando a chave "warnings_dialog".
        """
        config = load_warnings_config()
        if config:
            # Carrega e aplica a geometria (posição e tamanho)
            geom = config.get("geometry", None)
            if geom:
                try:
                    x = geom.get("x", 100)
                    y = geom.get("y", 100)
                    width = geom.get("width", 600)
                    height = geom.get("height", 400)
                    self.setGeometry(x, y, width, height)
                except Exception as e:
                    print("Error setting geometry:", e)
            # Carrega a largura das colunas
            col_widths = config.get("column_widths", [])
            if col_widths and len(col_widths) == self.table.columnCount():
                for i, w in enumerate(col_widths):
                    self.table.setColumnWidth(i, w)
            # Carrega a ordem das colunas
            col_order = config.get("column_order", [])
            if col_order and len(col_order) == self.table.columnCount():
                header = self.table.horizontalHeader()
                for visual_index, logical_index in enumerate(col_order):
                    if header.visualIndex(logical_index) != visual_index:
                        header.moveSection(header.visualIndex(logical_index), visual_index)

    def closeEvent(self, event):
        """
        Ao fechar, salva a configuração do diálogo (geometria e configurações das colunas)
        no arquivo de configuração do AppData, na chave "warnings_dialog".
        """
        geom = self.geometry()
        config = {
            "geometry": {
                "x": geom.x(),
                "y": geom.y(),
                "width": geom.width(),
                "height": geom.height()
            },
            "column_widths": [],
            "column_order": []
        }
        for i in range(self.table.columnCount()):
            config["column_widths"].append(self.table.horizontalHeader().sectionSize(i))
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            config["column_order"].append(header.logicalIndex(i))
        save_warnings_config(config)
        super().closeEvent(event)
