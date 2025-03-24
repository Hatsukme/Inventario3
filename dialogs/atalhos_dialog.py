# atalhos_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class atalhosDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Atalhos")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Cria um label com a lista de atalhos
        texto_atalhos = (
            "Ctrl+N: Adicionar novo item\n"
            "Ctrl+S: Salvar alterações\n"
            "Ctrl+L: Selecionar o último item da tabela\n"
            "Ctrl+H: Selecionar o primeiro item da tabela\n"
            "F5: Atualizar diretório e tabela\n"
            "Ctrl+Z: Desfazer até 5 alterações (inserção ou exclusão)\n"

        )
        label = QLabel(texto_atalhos)
        layout.addWidget(label)

