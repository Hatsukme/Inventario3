import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QMessageBox
)
from database import obter_conexao

from .image_enlarge_dialog import ImageEnlargeDialog


class ItemDetailDialog(QDialog):
    """
    Diálogo que exibe os detalhes de um item (título, responsável, quantidade, descrição, imagem).
    """

    def __init__(self, parent=None, item_id=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Item")
        self.resize(450, 500)
        layout = QVBoxLayout(self)

        self.label_title = QLabel()
        self.label_responsible = QLabel()
        self.label_quantity = QLabel()

        layout.addWidget(self.label_title)
        layout.addWidget(self.label_responsible)
        layout.addWidget(self.label_quantity)

        self.text_description = QTextEdit()
        self.text_description.setReadOnly(True)
        layout.addWidget(self.text_description)

        self.img_label = QLabel()
        self.img_label.setFixedSize(200, 200)
        self.img_label.setStyleSheet("border: 1px solid gray;")
        self.img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img_label)

        btn_enlarge = QPushButton("Ampliar Imagem")
        btn_enlarge.clicked.connect(self.ampliar_imagem)
        layout.addWidget(btn_enlarge)

        self.image_path = None
        self.load_item(item_id)

    def load_item(self, item_id):
        if not item_id:
            return
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, responsible, quantity, description, image_path
                      FROM items
                     WHERE id = ?
                """, (item_id,))
                row = cursor.fetchone()
            if row:
                title, responsible, quantity, description, image_path = row
                self.label_title.setText(f"<b>Título:</b> {title}")
                self.label_responsible.setText(f"<b>Responsável:</b> {responsible}")
                self.label_quantity.setText(f"<b>Quantidade:</b> {quantity}")
                self.text_description.setText(description or "")
                self.image_path = image_path
                if self.image_path and os.path.exists(self.image_path):
                    pixmap = QPixmap(self.image_path)
                    self.img_label.setPixmap(pixmap.scaled(
                        self.img_label.size(),
                        Qt.KeepAspectRatio
                    ))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar detalhes do item: {e}")

    def ampliar_imagem(self):
        if not self.image_path or not os.path.exists(self.image_path):
            QMessageBox.information(self, "Informação", "Não há imagem para ampliar.")
            return
        dlg = ImageEnlargeDialog(self, self.image_path)
        dlg.exec_()
