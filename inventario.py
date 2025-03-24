import sys
import ctypes

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui

from main_window import MainWindow

def main():
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Define ícone da aplicação (ajuste o caminho se necessário)
    icon = QtGui.QIcon("icone.png")
    app.setWindowIcon(icon)

    # Define ID do aplicativo no Windows (para agrupar janelas na barra de tarefas)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("inventario.v1")

    # Instancia e exibe a janela principal
    window = MainWindow()
    window.show()

    # Executa o loop da aplicação
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()