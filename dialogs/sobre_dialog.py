# sobre_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class dialog_about(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sobre")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Cria um label com a lista de atalhos
        texto_atalhos = (
            "O programa, ao ser executado, sempre ira verificar se existe o arquivo inventário.db no mesmo diretório do .exe\n"
            "Se não existir, ele criará. Se já existir, o programa o utilizará.\n"
            "O mesmo vale para a pasta de imagens (imagens_originais).\n"
            "\n"
            "Todos os arquivos de backup, csv e imagens, são armazenados no mesmo dirtório do executavel.\n"
            "Exceto o de config, pois ele dita a preferência salva pelo usuario. Este fica salvo no %appdata% de cada usuário.\n"
        )
        label = QLabel(texto_atalhos)
        layout.addWidget(label)