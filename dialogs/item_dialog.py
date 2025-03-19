import os
import shutil

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QLabel,
    QPushButton, QSpinBox, QFileDialog, QHBoxLayout, QMessageBox, QShortcut
)
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from database import obter_conexao, IMAGES_FOLDER

class CopyImageThread(QThread):
    """
    Thread para copiar a imagem em segundo plano,
    evitando congelar a interface se for um arquivo grande.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(Exception)

    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination

    def run(self):
        try:
            shutil.copy(self.source, self.destination)
            self.finished.emit(self.destination)
        except Exception as e:
            self.error.emit(e)


class ItemDialog(QDialog):
    """
    Diálogo para adicionar/editar um item de inventário.
    """
    def __init__(self, parent=None, item_id=None, directory_id=None):
        super().__init__(parent)
        self.copy_thread = None
        self.setWindowTitle("Item de Inventário")
        self.item_id = item_id
        self.directory_id = directory_id
        self.image_path = None

        self.resize(400, 400)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        self.title_edit = QLineEdit()
        form_layout.addRow("Título:", self.title_edit)

        self.responsible_edit = QLineEdit()
        form_layout.addRow("Responsável:", self.responsible_edit)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        form_layout.addRow("Quantidade:", self.quantity_spin)

        self.description_edit = QTextEdit()
        form_layout.addRow("Descrição:", self.description_edit)

        self.img_label = QLabel()
        self.img_label.setFixedSize(150, 150)
        self.img_label.setStyleSheet("border: 1px solid gray;")
        self.img_label.setAlignment(Qt.AlignCenter)

        btn_select_image = QPushButton("Selecionar Imagem")
        btn_select_image.clicked.connect(self.selecionar_imagem)

        img_layout = QHBoxLayout()
        img_layout.addWidget(self.img_label)
        img_layout.addWidget(btn_select_image)
        form_layout.addRow("Imagem:", img_layout)

        # Se item_id existe, carregamos dados do items
        if self.item_id:
            try:
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT title, responsible, quantity, description, image_path, directory_id
                          FROM items
                         WHERE id = ?
                    """, (self.item_id,))
                    row = cursor.fetchone()
                if row:
                    self.title_edit.setText(row[0])
                    self.responsible_edit.setText(row[1])
                    self.quantity_spin.setValue(row[2] or 0)
                    self.description_edit.setPlainText(row[3] or "")
                    self.image_path = row[4]
                    self.directory_id = row[5]
                    if self.image_path and os.path.exists(self.image_path):
                        pixmap = QPixmap(self.image_path)
                        self.img_label.setPixmap(pixmap.scaled(
                            self.img_label.size(),
                            Qt.KeepAspectRatio
                        ))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar item: {e}")

        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self.salvar_item)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)


        #Atalhos===========================
        #Salvar itens
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        saveShortcut.activated.connect(self.salvar_item)

    def selecionar_imagem(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            original_filename = os.path.basename(file_path)
            dest_path = os.path.join(IMAGES_FOLDER, original_filename)
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(original_filename)
                counter = 1
                while os.path.exists(os.path.join(IMAGES_FOLDER, f"{base}_{counter}{ext}")):
                    counter += 1
                dest_path = os.path.join(IMAGES_FOLDER, f"{base}_{counter}{ext}")

            self.copy_thread = CopyImageThread(file_path, dest_path)
            self.copy_thread.finished.connect(self.on_image_copied)
            self.copy_thread.error.connect(lambda e: QMessageBox.critical(self, "Erro", f"Falha ao copiar imagem: {e}"))
            self.copy_thread.start()

    def on_image_copied(self, dest_path):
        self.image_path = dest_path
        pixmap = QPixmap(self.image_path)
        self.img_label.setPixmap(pixmap.scaled(
            self.img_label.size(),
            Qt.KeepAspectRatio
        ))

    def salvar_item(self):
        title = self.title_edit.text().strip()
        responsible = self.responsible_edit.text().strip()
        quantity = self.quantity_spin.value()
        description = self.description_edit.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "Atenção", "O campo Título é obrigatório.")
            return

        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                if self.item_id:
                    cursor.execute("""
                        UPDATE items
                           SET title = ?,
                               responsible = ?,
                               quantity = ?,
                               description = ?,
                               image_path = ?
                         WHERE id = ?
                    """, (title, responsible, quantity, description, self.image_path, self.item_id))
                else:
                    cursor.execute("""
                        INSERT INTO items (title, responsible, quantity, description, image_path, directory_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (title, responsible, quantity, description, self.image_path, self.directory_id))
                conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar item: {e}")

