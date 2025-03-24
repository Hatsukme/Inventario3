# atalho.py
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence


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
    # Atalho para adicionar item na main_window
    shortcutAddItem = QShortcut(QKeySequence("Ctrl+N"), main_window)
    shortcutAddItem.activated.connect(main_window.adicionar_item)

    # Se o diálogo for fornecido, configurar o atalho para salvar nele.
    if item_dialog is not None:
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), item_dialog)
        saveShortcut.activated.connect(item_dialog.salvar_item)

    # Novo atalho: Ctrl+L para posicionar no último item da tabela
    shortcutLastItem = QShortcut(QKeySequence("Ctrl+L"), main_window)
    shortcutLastItem.activated.connect(main_window.posicionar_ultimo_item)

    # Novo atalho: Ctrl+H para posicionar no primeiro item da tabela
    shortcutFirstItem = QShortcut(QKeySequence("Ctrl+H"), main_window)
    shortcutFirstItem.activated.connect(main_window.posicionar_primeiro_item)

    # Novo atalho: F5 para atualizar (mesma função do botão de atualizar)
    shortcutUpdate = QShortcut(QKeySequence("F5"), main_window)
    shortcutUpdate.activated.connect(main_window.atualizar_diretorio_e_tabela)

    # Novo atalho: Ctrl+Z para desfazer até 5 alterações (inserção ou exclusão)
    shortcutUndo = QShortcut(QKeySequence("Ctrl+Z"), main_window)
    shortcutUndo.activated.connect(main_window.undo_last_action)