# atalho.py
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut


def setup_shortcuts(main_window, item_dialog=None):
    """
    Configura os atalhos para a aplicação.

    Atalhos definidos:
      - Ctrl+N: Adicionar novo item (na janela principal)
      - Ctrl+S: Salvar item (no diálogo, se fornecido)
      - Ctrl+L: Selecionar o último item da tabela
      - Ctrl+H: Selecionar o primeiro item da tabela
      - F5: Atualizar diretório e tabela
      - Ctrl+Z: Desfazer até 5 alterações (inserção ou exclusão)
    """
    # Atalho Ctrl+N para adicionar item
    shortcutAddItem = QShortcut(QKeySequence("Ctrl+N"), main_window)
    shortcutAddItem.activated.connect(main_window.add_item)

    # Se o diálogo for fornecido, configurar o atalho para salvar nele.
    if item_dialog is not None:
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), item_dialog)
        saveShortcut.activated.connect(item_dialog.save_item)

    # Atalho Ctrl+L para selecionar o último item
    shortcutLastItem = QShortcut(QKeySequence("Ctrl+L"), main_window)
    shortcutLastItem.activated.connect(main_window.select_last_item)

    # Atalho Ctrl+H para selecionar o primeiro item
    shortcutFirstItem = QShortcut(QKeySequence("Ctrl+H"), main_window)
    shortcutFirstItem.activated.connect(main_window.select_first_item)

    # Atalho F5 para atualizar
    shortcutRefresh = QShortcut(QKeySequence("F5"), main_window)
    shortcutRefresh.activated.connect(main_window.refresh_tree_and_table)

    # Atalho Ctrl+Z para desfazer
    shortcutUndo = QShortcut(QKeySequence("Ctrl+Z"), main_window)
    shortcutUndo.activated.connect(main_window.undo_last_action)
