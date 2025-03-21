import os
import json
import csv
import zipfile
import sys

from PyQt5.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QHeaderView,
                             QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
                             QPushButton, QFileDialog, QLabel, QLineEdit, QTextEdit, QSpinBox,
                             QMessageBox, QDialog, QFormLayout, QComboBox, QMenu, QAction, QScrollArea,
                             QHeaderView, QColorDialog, QCompleter, QToolButton, QStyle, QFrame, QShortcut
                             )
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPalette, QColor, QKeySequence
from PyQt5 import QtWidgets

from database import (
    verificar_ou_criar_db, criar_pasta_imagens, obter_conexao,
    NOME_DB, IMAGES_FOLDER
)
from config import get_config_path
from dialogs.directory_dialog import DirectoryDialog
from dialogs.item_dialog import ItemDialog
from dialogs.item_detail_dialog import ItemDetailDialog
from dialogs.move_item_dialog import MoveItemDialog
from widgets.quantity_widget import QuantityWidget
from database import set_database_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventário")

        # Verifica/cria o DB e a pasta de imagens
        verificar_ou_criar_db()
        criar_pasta_imagens()

        # Carrega as configurações (tema, posição da janela etc.)
        self.load_config()

        # Cria a barra de menu
        self.setup_menu()

        # Variáveis para pesquisa de diretórios
        self.current_search_text = ""
        self.current_search_results = []
        self.current_search_index = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Layout de pesquisa
        pesquisa_layout = QHBoxLayout()
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText(
            "Pesquisar por título, descrição, responsável ou diretório..."
        )
        self.search_line_edit.returnPressed.connect(self.pesquisar_itens)

        btn_search = QPushButton("Pesquisar")
        btn_search.clicked.connect(self.pesquisar_itens)

        btn_clear = QPushButton("Limpar Pesquisa")
        btn_clear.clicked.connect(self.limpar_pesquisa)

        pesquisa_layout.addWidget(self.search_line_edit)
        pesquisa_layout.addWidget(btn_search)
        pesquisa_layout.addWidget(btn_clear)
        main_layout.addLayout(pesquisa_layout)

        # Splitter para árvore de diretórios e tabela de itens
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Árvore de diretórios
        self.tree_directories = QTreeWidget()
        self.tree_directories.setHeaderLabel("Diretórios")
        self.tree_directories.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_directories.customContextMenuRequested.connect(self.on_tree_context_menu)
        self.tree_directories.itemClicked.connect(self.on_directory_selected)
        self.tree_directories.header().setStretchLastSection(False)
        self.tree_directories.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_directories.setDragEnabled(True)
        self.tree_directories.viewport().setAcceptDrops(True)
        self.tree_directories.setDropIndicatorShown(True)
        self.tree_directories.setDefaultDropAction(Qt.MoveAction)
        self.tree_directories.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree_directories.setDragDropMode(QTreeWidget.InternalMove)

        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)

        # Barra de ferramentas para expandir/retrair
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(5)

        btn_expand = QToolButton()
        btn_expand.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        btn_expand.setToolTip("Expandir")
        btn_expand.clicked.connect(self.tree_directories.expandAll)
        control_layout.addWidget(btn_expand)

        btn_collapse = QToolButton()
        btn_collapse.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        btn_collapse.setToolTip("Retrair")
        btn_collapse.clicked.connect(self.tree_directories.collapseAll)
        control_layout.addWidget(btn_collapse)

        control_layout.addStretch()

        btn_update = QToolButton()
        btn_update.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        btn_update.setToolTip("Atualizar")
        btn_update.clicked.connect(self.atualizar_diretorio_e_tabela)
        control_layout.addWidget(btn_update)

        tree_layout.addWidget(control_frame)

        # Campo de pesquisa de diretórios
        self.dir_search_line_edit = QLineEdit()
        self.dir_search_line_edit.setPlaceholderText("Pesquisar Diretório...")
        self.dir_search_line_edit.returnPressed.connect(self.pesquisar_diretorio)
        tree_layout.addWidget(self.dir_search_line_edit)

        tree_layout.addWidget(self.tree_directories)
        splitter.addWidget(tree_container)

        # Tabela de itens
        self.table_items = QTableWidget()
        self.table_items.setColumnCount(6)
        self.table_items.setHorizontalHeaderLabels(["ID", "Título", "Responsável", "Quantidade", "Imagem", "Descrição"])
        self.table_items.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_items.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_items.customContextMenuRequested.connect(self.on_table_context_menu)
        self.table_items.cellDoubleClicked.connect(self.on_item_double_clicked)
        self.table_items.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_items.horizontalHeader().setSectionsMovable(True)
        self.table_items.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_items.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_items.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        splitter.addWidget(self.table_items)

        header = self.table_items.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.header_context_menu)

        # Ajusta tamanhos iniciais do splitter
        splitter.setSizes([200, 600])

        # Botão para adicionar item
        self.btn_add_item = QPushButton("Adicionar Item")
        self.btn_add_item.clicked.connect(self.adicionar_item)
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

        # Carrega a árvore
        self.carregar_arvore()
        # Restaura configurações da tabela
        self.restore_table_config()

        #Atalhos====================================
        #Novo item
        shortcutAddItem = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcutAddItem.activated.connect(self.adicionar_item)

    def header_context_menu(self, pos):
        header = self.table_items.horizontalHeader()
        # Obtém o índice lógico da coluna a partir da posição do clique
        logical_index = header.logicalIndexAt(pos)
        if logical_index < 0:
            return

        menu = QMenu(self)
        action_asc = menu.addAction("Crescente")
        action_desc = menu.addAction("Decrescente")

        action = menu.exec_(header.mapToGlobal(pos))
        if action == action_asc:
            self.table_items.sortItems(logical_index, Qt.AscendingOrder)
        elif action == action_desc:
            self.table_items.sortItems(logical_index, Qt.DescendingOrder)

    # --------------------------------------------------
    # Carregamento e salvamento de configurações
    # --------------------------------------------------

    def load_config(self):
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                window_conf = config.get("window", {})
                if window_conf:
                    self.resize(
                        window_conf.get("width", self.width()),
                        window_conf.get("height", self.height())
                    )
                    self.move(
                        window_conf.get("x", self.x()),
                        window_conf.get("y", self.y())
                    )
                self.tree_colors = config.get("tree", {}).get("colors", {})
                self.expanded_ids = config.get("tree", {}).get("expanded", [])
                self.table_config = config.get("table", {})
                self.tema_atual = config.get("theme", "claro")

                if self.tema_atual == "escuro":
                    self.apply_dark_theme()
                else:
                    self.apply_light_theme()

            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"Não foi possível carregar as configurações: {e}")

    def save_config(self):
        from database import NOME_DB  # NOME_DB contém o caminho atual do banco
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
            "theme": getattr(self, "tema_atual", "claro")
        }
        try:
            with open(get_config_path(), "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível salvar as configurações: {e}")

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)


    # --------------------------------------------------
    # Menu superior
    # --------------------------------------------------

    def setup_menu(self):
        menubar = self.menuBar()

        # Menu CSV
        menu_csv = menubar.addMenu("CSV")

        acao_exportar_csv = QAction("Exportar Banco para CSV", self)
        acao_exportar_csv.triggered.connect(self.exportar_csv)
        menu_csv.addAction(acao_exportar_csv)

        acao_importar_csv = QAction("Importar Banco de CSV", self)
        acao_importar_csv.triggered.connect(self.importar_csv)
        menu_csv.addAction(acao_importar_csv)

        # Menu Backup
        menu_backup = menubar.addMenu("Backup")

        acao_backup_banco = QAction("Backup do Banco", self)
        acao_backup_banco.triggered.connect(self.backup_banco)
        menu_backup.addAction(acao_backup_banco)

        acao_backup_imagens = QAction("Backup das Imagens", self)
        acao_backup_imagens.triggered.connect(self.backup_imagens)
        menu_backup.addAction(acao_backup_imagens)

        acao_backup_configs = QAction("Backup das Configs", self)
        acao_backup_configs.triggered.connect(self.backup_configs)
        menu_backup.addAction(acao_backup_configs)

        # Menu Configurações
        menu_config = menubar.addMenu("Configurações")

        acao_importar_config = QAction("Importar Config", self)
        acao_importar_config.triggered.connect(self.importar_config)
        menu_config.addAction(acao_importar_config)

        acao_trocar_tema = QAction("Trocar Tema (Escuro/Claro)", self)
        acao_trocar_tema.triggered.connect(self.trocar_tema)
        menu_config.addAction(acao_trocar_tema)

        # Ação para conectar em outro banco:
        action_conectar_db = QAction("Conectar em outro banco", self)
        action_conectar_db.triggered.connect(self.selecionar_banco)
        menu_config.addAction(action_conectar_db)

    def selecionar_banco(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar Banco de Dados", "", "SQLite DB (*.db)")
        if caminho:
            from database import set_database_path, criar_pasta_imagens
            set_database_path(caminho)
            criar_pasta_imagens()  # Cria o diretório de imagens para o novo banco, se necessário
            print("Banco selecionado:", caminho)
            self.carregar_arvore()

    # --------------------------------------------------
    # Árvores e diretórios
    # --------------------------------------------------

    def carregar_arvore(self):
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
                        # Se tivermos cor salva para este diretório
                        if hasattr(self, "tree_colors") and str(d_id) in self.tree_colors:
                            color = QColor(self.tree_colors[str(d_id)])
                            item.setBackground(0, color)
                        parent_item.addChild(item)
                        add_children(item, d_id)

            root_item = self.tree_directories.invisibleRootItem()
            for d_id, (d_name, d_parent) in dirs.items():
                if d_parent is None:
                    item = QTreeWidgetItem([d_name])
                    item.setData(0, Qt.UserRole, d_id)
                    if hasattr(self, "tree_colors") and str(d_id) in self.tree_colors:
                        color = QColor(self.tree_colors[str(d_id)])
                        item.setBackground(0, color)
                    root_item.addChild(item)
                    add_children(item, d_id)

            if hasattr(self, "expanded_ids"):
                self.restore_tree_expansion(self.expanded_ids)

            self.update_dir_completer()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar árvore de diretórios: {e}")

    def on_directory_selected(self, item, column):
        directory_id = item.data(0, Qt.UserRole)
        self.carregar_itens_do_diretorio(directory_id)

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

    # --------------------------------------------------
    # Completer de diretórios (pesquisa)
    # --------------------------------------------------

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

    def pesquisar_diretorio(self):
        texto = self.dir_search_line_edit.text().strip().lower()
        if not texto:
            return
        if texto != self.current_search_text or not self.current_search_results:
            self.current_search_text = texto
            self.current_search_results = [path for path in self.dir_path_map if texto in path.lower()]
            self.current_search_index = 0
        else:
            self.current_search_index += 1
            if self.current_search_index >= len(self.current_search_results):
                self.current_search_index = 0

        if self.current_search_results:
            match = self.current_search_results[self.current_search_index]
            self.on_dir_completer_activated(match)
        else:
            QMessageBox.information(
                self,
                "Diretório não encontrado",
                f"O diretório '{texto}' não foi localizado."
            )

    # --------------------------------------------------
    # Context menu da árvore de diretórios
    # --------------------------------------------------

    def on_tree_context_menu(self, pos: QPoint):
        item = self.tree_directories.itemAt(pos)
        menu = QMenu(self)

        if item:
            action_add_dir = QAction("Adicionar Subdiretório", self)
            action_add_dir.triggered.connect(self.adicionar_subdiretorio)
            menu.addAction(action_add_dir)

            action_edit_dir = QAction("Editar Diretório", self)
            action_edit_dir.triggered.connect(self.editar_diretorio)
            menu.addAction(action_edit_dir)

            action_move_dir = QAction("Mover Diretório", self)
            action_move_dir.triggered.connect(self.mover_diretorio)
            menu.addAction(action_move_dir)

            action_del_dir = QAction("Excluir Diretório", self)
            action_del_dir.triggered.connect(self.excluir_diretorio)
            menu.addAction(action_del_dir)

            action_visualizar = QAction("Visualizar Itens (recursivo)", self)
            action_visualizar.triggered.connect(self.visualizar_itens)
            menu.addAction(action_visualizar)

            action_set_color = QAction("Definir Cor", self)
            action_set_color.triggered.connect(lambda: self.definir_cor(item))
            menu.addAction(action_set_color)

            # Se já tiver cor, permitir remover
            dir_id = item.data(0, Qt.UserRole)
            if hasattr(self, "tree_colors") and str(dir_id) in self.tree_colors:
                action_remove_color = QAction("Remover Cor", self)
                action_remove_color.triggered.connect(lambda: self.remover_cor(item))
                menu.addAction(action_remove_color)

        else:
            # Clique na área vazia da árvore
            action_add_root = QAction("Adicionar Diretório Raiz", self)
            action_add_root.triggered.connect(self.adicionar_diretorio_raiz)
            menu.addAction(action_add_root)

        menu.exec_(self.tree_directories.mapToGlobal(pos))

    def adicionar_diretorio_raiz(self):
        dialog = DirectoryDialog(self, parent_directory_id=None)
        if dialog.exec_() == QDialog.Accepted:
            # Salva o estado atual da árvore antes de recarregar
            self.expanded_ids = self.get_expanded_items()
            self.carregar_arvore()

    def adicionar_subdiretorio(self):
        parent_id = self.get_selected_directory_id()
        if not parent_id:
            QMessageBox.warning(self, "Atenção", "Selecione um diretório para adicionar subdiretório.")
            return
        dialog = DirectoryDialog(self, parent_directory_id=parent_id)
        if dialog.exec_() == QDialog.Accepted:
            # Salva o estado atual da árvore antes de recarregar
            self.expanded_ids = self.get_expanded_items()
            self.carregar_arvore()

    def editar_diretorio(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Atenção", "Selecione um diretório para editar.")
            return
        dialog = DirectoryDialog(self, directory_id=directory_id)
        if dialog.exec_() == QDialog.Accepted:
            self.carregar_arvore()

    def mover_diretorio(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Atenção", "Selecione um diretório para mover.")
            return
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM directories WHERE id != ?", (directory_id,))
                all_dirs = cursor.fetchall()
            dlg = QDialog(self)
            dlg.setWindowTitle("Mover Diretório")
            layout = QVBoxLayout(dlg)

            combo = QComboBox()
            combo.addItem("Raiz (sem pai)", None)
            for d_id, d_name in all_dirs:
                combo.addItem(d_name, d_id)
            layout.addWidget(combo)

            btn_layout = QHBoxLayout()
            layout.addLayout(btn_layout)

            btn_ok = QPushButton("OK")
            btn_ok.clicked.connect(dlg.accept)
            btn_layout.addWidget(btn_ok)

            btn_cancel = QPushButton("Cancelar")
            btn_cancel.clicked.connect(dlg.reject)
            btn_layout.addWidget(btn_cancel)

            if dlg.exec_() == QDialog.Accepted:
                new_parent_id = combo.currentData()
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE directories SET parent_id = ? WHERE id = ?", (new_parent_id, directory_id))
                    conn.commit()
                self.carregar_arvore()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao mover diretório: {e}")

    def excluir_diretorio(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Atenção", "Selecione um diretório para excluir.")
            return
        resposta = QMessageBox.question(
            self, "Confirmação",
            "Deseja realmente excluir este diretório e todo o conteúdo dentro dele?"
        )
        if resposta != QMessageBox.Yes:
            return
        self.excluir_diretorio_recursivo(directory_id)
        self.carregar_arvore()
        self.table_items.setRowCount(0)

    def excluir_diretorio_recursivo(self, directory_id):
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                # Exclui subdiretórios
                cursor.execute("SELECT id FROM directories WHERE parent_id = ?", (directory_id,))
                subdirs = cursor.fetchall()
                for sd in subdirs:
                    self.excluir_diretorio_recursivo(sd[0])

                # Exclui itens
                cursor.execute("DELETE FROM items WHERE directory_id = ?", (directory_id,))
                # Exclui o diretório em si
                cursor.execute("DELETE FROM directories WHERE id = ?", (directory_id,))
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir diretório: {e}")

    def definir_cor(self, item):
        color = QColorDialog.getColor()
        if color.isValid():
            item.setBackground(0, color)
            if not hasattr(self, "tree_colors"):
                self.tree_colors = {}
            dir_id = item.data(0, Qt.UserRole)
            self.tree_colors[str(dir_id)] = color.name()

    def remover_cor(self, item):
        dir_id = item.data(0, Qt.UserRole)
        if hasattr(self, "tree_colors") and str(dir_id) in self.tree_colors:
            del self.tree_colors[str(dir_id)]
        item.setBackground(0, QColor())

    def visualizar_itens(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Atenção", "Selecione um diretório.")
            return
        self.carregar_itens_recursivo(directory_id)

    # --------------------------------------------------
    # Itens
    # --------------------------------------------------

    def carregar_itens_do_diretorio(self, directory_id):
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
                ["ID", "Título", "Responsável", "Quantidade", "Imagem", "Descrição"]
            )
            self.table_items.setRowCount(len(rows))

            for i, row in enumerate(rows):
                item_id, title, resp, qty, image_path, desc = row

                self.table_items.setItem(i, 0, QTableWidgetItem(str(item_id)))
                self.table_items.setItem(i, 1, QTableWidgetItem(title))
                self.table_items.setItem(i, 2, QTableWidgetItem(resp or ""))

                # Usa nosso widget customizado de quantidade
                from widgets.quantity_widget import QuantityWidget
                quantity = qty if qty is not None else 0
                quantity_widget = QuantityWidget(item_id, quantity)
                self.table_items.setCellWidget(i, 3, quantity_widget)

                self.table_items.setItem(i, 4, QTableWidgetItem("Sim" if image_path else "Não"))
                self.table_items.setItem(i, 5, QTableWidgetItem(desc or ""))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar itens: {e}")

    def carregar_itens_recursivo(self, directory_id):
        query = """
        WITH RECURSIVE subdirs(id) AS (
            SELECT id FROM directories WHERE id = ?
            UNION ALL
            SELECT d.id FROM directories d
             JOIN subdirs s ON d.parent_id = s.id
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
                ["ID", "Título", "Responsável", "Quantidade", "Imagem", "Descrição", "Diretório"]
            )
            self.table_items.setRowCount(len(rows))

            for i, row in enumerate(rows):
                item_id, title, resp, qty, image_path, dir_name, desc = row

                self.table_items.setItem(i, 0, QTableWidgetItem(str(item_id)))
                self.table_items.setItem(i, 1, QTableWidgetItem(title))
                self.table_items.setItem(i, 2, QTableWidgetItem(resp or ""))

                # Usa nosso widget customizado
                from widgets.quantity_widget import QuantityWidget
                quantity = qty if qty is not None else 0
                quantity_widget = QuantityWidget(item_id, quantity)
                self.table_items.setCellWidget(i, 3, quantity_widget)

                self.table_items.setItem(i, 4, QTableWidgetItem("Sim" if image_path else "Não"))
                self.table_items.setItem(i, 5, QTableWidgetItem(desc or ""))
                self.table_items.setItem(i, 6, QTableWidgetItem(dir_name or ""))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar itens recursivamente: {e}")

    def adicionar_item(self):
        directory_id = self.get_selected_directory_id()
        if not directory_id:
            QMessageBox.warning(self, "Atenção", "Selecione um diretório para adicionar item.")
            return
        dlg = ItemDialog(self, directory_id=directory_id)
        if dlg.exec_() == QDialog.Accepted:
            self.carregar_itens_do_diretorio(directory_id)

            self.table_items.scrollToBottom()

    def get_selected_item_id(self):
        row = self.table_items.currentRow()
        if row < 0:
            return None
        item_id_item = self.table_items.item(row, 0)
        if item_id_item:
            return item_id_item.text()
        return None

    def editar_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Atenção", "Selecione um item para editar.")
            return
        directory_id = self.get_selected_directory_id()
        dlg = ItemDialog(self, item_id=int(item_id))
        if dlg.exec_() == QDialog.Accepted:
            self.carregar_itens_do_diretorio(directory_id)

    def atualizar_tabela(self):
        # Verifica se há um diretório selecionado e recarrega os itens
        directory_id = self.get_selected_directory_id()
        if directory_id:
            self.carregar_itens_do_diretorio(directory_id)
        else:
            self.table_items.setRowCount(0)

    def atualizar_diretorio_e_tabela(self):
        # Armazena o ID do diretório selecionado antes de atualizar a árvore
        selected_directory_id = self.get_selected_directory_id()

        # Atualiza a árvore de diretórios
        self.carregar_arvore()

        # Tenta re-selecionar o diretório que estava selecionado
        if selected_directory_id:
            # Função auxiliar para buscar o item na árvore
            def buscar_item_por_id(item, dir_id):
                if item.data(0, Qt.UserRole) == dir_id:
                    return item
                for i in range(item.childCount()):
                    resultado = buscar_item_por_id(item.child(i), dir_id)
                    if resultado:
                        return resultado
                return None

            root = self.tree_directories.invisibleRootItem()
            found_item = None
            for i in range(root.childCount()):
                found_item = buscar_item_por_id(root.child(i), selected_directory_id)
                if found_item:
                    break

            if found_item:
                self.tree_directories.setCurrentItem(found_item)

        # Atualiza a tabela dos itens com base no diretório (possivelmente re-selecionado)
        self.atualizar_tabela()

    def excluir_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Atenção", "Selecione um item para excluir.")
            return
        resposta = QMessageBox.question(self, "Confirmação", "Deseja realmente excluir este item?")
        if resposta != QMessageBox.Yes:
            return
        try:
            directory_id = self.get_selected_directory_id()
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
                conn.commit()
            # Atualiza a tabela de itens após a exclusão
            self.atualizar_tabela()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir item: {e}")

    def mover_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Atenção", "Selecione um item para mover.")
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
                    self.carregar_itens_do_diretorio(self.get_selected_directory_id())
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao mover item: {e}")

    def duplicar_item(self):
        item_id = self.get_selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Atenção", "Selecione um item para duplicar.")
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
                    new_title = f"Cópia de {title}"
                    cursor.execute("""
                        INSERT INTO items (title, responsible, quantity, description, image_path, directory_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_title, responsible, quantity, description, image_path, directory_id))
                    conn.commit()

            current_dir_id = self.get_selected_directory_id()
            if current_dir_id:
                self.carregar_itens_do_diretorio(current_dir_id)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao duplicar item: {e}")

    def on_item_double_clicked(self, row, column):
        item_id = self.get_selected_item_id()
        if item_id:
            dlg = ItemDetailDialog(self, item_id=int(item_id))
            dlg.exec_()

    def on_table_context_menu(self, pos: QPoint):
        row = self.table_items.rowAt(pos.y())
        menu = QMenu(self)

        action_add = QAction("Adicionar Item", self)
        action_add.triggered.connect(self.adicionar_item)
        menu.addAction(action_add)

        if row >= 0:
            action_edit = QAction("Editar Item", self)
            action_edit.triggered.connect(self.editar_item)
            menu.addAction(action_edit)

            action_del = QAction("Excluir Item", self)
            action_del.triggered.connect(self.excluir_item)
            menu.addAction(action_del)

            action_move = QAction("Mover Item", self)
            action_move.triggered.connect(self.mover_item)
            menu.addAction(action_move)

            action_duplicate = QAction("Duplicar Item", self)
            action_duplicate.triggered.connect(self.duplicar_item)
            menu.addAction(action_duplicate)

        menu.exec_(self.table_items.mapToGlobal(pos))

    # --------------------------------------------------
    # Pesquisa de itens
    # --------------------------------------------------

    def pesquisar_itens(self):
        termo = self.search_line_edit.text().strip()
        if not termo:
            return
        like_term = f"%{termo}%"
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
                ["ID", "Título", "Responsável", "Quantidade", "Imagem", "Descrição", "Diretório"]
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

                self.table_items.setItem(i, 4, QTableWidgetItem("Sim" if image_path else "Não"))
                self.table_items.setItem(i, 5, QTableWidgetItem(desc or ""))
                self.table_items.setItem(i, 6, QTableWidgetItem(dir_name or ""))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao pesquisar itens: {e}")

    def limpar_pesquisa(self):
        self.search_line_edit.clear()
        directory_id = self.get_selected_directory_id()
        if directory_id:
            self.carregar_itens_do_diretorio(directory_id)
        else:
            self.table_items.setRowCount(0)

    # --------------------------------------------------
    # Funções de CSV e Backup
    # --------------------------------------------------

    def exportar_csv(self):
        try:
            caminho, _ = QFileDialog.getSaveFileName(self, "Exportar Banco para CSV", "", "CSV Files (*.csv)")
            if not caminho:
                return
            with obter_conexao() as conn:
                cursor = conn.cursor()
                # Diretórios
                cursor.execute("SELECT * FROM directories")
                diretorios = cursor.fetchall()
                dir_columns = [desc[0] for desc in cursor.description]

                # Itens
                cursor.execute("SELECT * FROM items")
                itens = cursor.fetchall()
                item_columns = [desc[0] for desc in cursor.description]

            with open(caminho, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["=== DIRECTORIES ==="])
                writer.writerow(dir_columns)
                for row in diretorios:
                    writer.writerow(row)
                writer.writerow([])
                writer.writerow(["=== ITEMS ==="])
                writer.writerow(item_columns)
                for row in itens:
                    writer.writerow(row)

            QMessageBox.information(self, "CSV", "Exportação para CSV concluída.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar CSV: {e}")

    def importar_csv(self):
        try:
            caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar CSV", "", "CSV Files (*.csv)")
            if not caminho:
                return

            with open(caminho, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                conteudo = list(reader)

            if not conteudo:
                QMessageBox.warning(self, "CSV", "Arquivo CSV vazio.")
                return

            # Localiza as seções
            try:
                idx_dir = conteudo.index(["=== DIRECTORIES ==="])
                idx_itens = conteudo.index(["=== ITEMS ==="])
            except ValueError:
                QMessageBox.warning(self, "CSV", "Formato CSV inválido (faltam seções).")
                return

            dir_headers = conteudo[idx_dir + 1]
            diretorios = conteudo[idx_dir + 2:idx_itens]
            item_headers = conteudo[idx_itens + 1]
            itens = conteudo[idx_itens + 2:]

            # Supondo colunas [id, name, parent_id] para diretórios
            idx_id_dir = 0
            idx_name_dir = 1
            idx_parent_dir = 2

            old_dirs = {}
            for row in diretorios:
                if not row:
                    continue
                old_id = int(row[idx_id_dir])
                name = row[idx_name_dir]
                parent_str = row[idx_parent_dir].strip() if len(row) > idx_parent_dir else ""
                if parent_str == "":
                    parent_id = None
                else:
                    parent_id = int(parent_str)
                old_dirs[old_id] = (name, parent_id)

            # Mapeamento old->new IDs
            id_map = {}

            def insert_dir(od_id, cursor):
                if od_id in id_map:
                    return id_map[od_id]
                nm, pid = old_dirs[od_id]
                if pid is None or pid not in old_dirs:
                    new_parent = None
                else:
                    new_parent = insert_dir(pid, cursor)

                cursor.execute("INSERT INTO directories (name, parent_id) VALUES (?, ?)", (nm, new_parent))
                new_id = cursor.lastrowid
                id_map[od_id] = new_id
                return new_id

            with obter_conexao() as conn:
                cursor = conn.cursor()
                for od_id in old_dirs:
                    insert_dir(od_id, cursor)
                conn.commit()

            # Agora, itens (supondo colunas [id, title, responsible, quantity, description, image_path, directory_id])
            idx_id_item = 0
            idx_title_item = 1
            idx_resp_item = 2
            idx_qty_item = 3
            idx_desc_item = 4
            idx_img_item = 5
            idx_dir_item = 6

            with obter_conexao() as conn:
                cursor = conn.cursor()
                for row in itens:
                    if not row:
                        continue
                    title = row[idx_title_item]
                    responsible = row[idx_resp_item]
                    qty_str = row[idx_qty_item].strip()
                    quantity = int(qty_str) if qty_str else None
                    description = row[idx_desc_item]
                    image_path = row[idx_img_item]
                    old_dir_str = row[idx_dir_item].strip()
                    if old_dir_str == "":
                        old_dir = None
                    else:
                        old_dir = int(old_dir_str)

                    new_dir = id_map.get(old_dir) if old_dir else None
                    cursor.execute("""
                            INSERT INTO items (title, responsible, quantity, description, image_path, directory_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (title, responsible, quantity, description, image_path, new_dir))
                conn.commit()

            QMessageBox.information(self, "CSV", "Importação concluída com sucesso.")
            self.carregar_arvore()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar CSV: {e}")

    def backup_banco(self):
        try:
            nome_zip = f"backup_banco_{os.path.splitext(os.path.basename(NOME_DB))[0]}.zip"
            with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(NOME_DB, os.path.basename(NOME_DB))
            QMessageBox.information(self, "Backup", f"Backup do banco criado: {nome_zip}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no backup do banco: {e}")

    def backup_imagens(self):
        try:
            nome_zip = f"backup_imagens_{os.path.basename(IMAGES_FOLDER)}.zip"
            with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for raiz, dirs, arquivos in os.walk(IMAGES_FOLDER):
                    for arq in arquivos:
                        caminho_completo = os.path.join(raiz, arq)
                        arcname = os.path.relpath(caminho_completo, os.path.dirname(IMAGES_FOLDER))
                        zipf.write(caminho_completo, arcname)
            QMessageBox.information(self, "Backup", f"Backup das imagens criado: {nome_zip}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no backup das imagens: {e}")

    def backup_configs(self):
        try:
            import datetime
            config_path = get_config_path()
            folder = os.path.dirname(config_path)
            nome_zip = os.path.join(
                folder,
                f"backup_configs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            )
            with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(config_path, os.path.basename(config_path))
            QMessageBox.information(self, "Backup", f"Backup das configs criado: {nome_zip}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no backup das configs: {e}")

    def importar_config(self):
        try:
            caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar Config", "", "JSON Files (*.json)")
            if not caminho:
                return
            destino = get_config_path()
            shutil.copy(caminho, destino)
            QMessageBox.information(self, "Config",
                                    "Config importada com sucesso. Reinicie a aplicação para aplicar as alterações.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar config: {e}")

    # --------------------------------------------------
    # Tema (Claro/Escuro)
    # --------------------------------------------------

    def trocar_tema(self):
        if getattr(self, "tema_atual", "claro") == "claro":
            self.tema_atual = "escuro"
            self.apply_dark_theme()
        else:
            self.tema_atual = "claro"
            self.apply_light_theme()
        self.salvar_config_tema()

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

    def salvar_config_tema(self):
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
            QMessageBox.warning(self, "Aviso", f"Não foi possível salvar o tema na configuração: {e}")

    # --------------------------------------------------
    # Restaura configurações da tabela (largura e ordem)
    # --------------------------------------------------

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