from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QHBoxLayout,
    QPushButton, QMessageBox
)
from database import obter_conexao

class DirectoryDialog(QDialog):
    """
    Diálogo para adicionar/editar um diretório.
    """
    def __init__(self, parent=None, directory_id=None, parent_directory_id=None):
        super().__init__(parent)
        self.setWindowTitle("Diretório")
        self.directory_id = directory_id
        self.parent_directory_id = parent_directory_id
        self.resize(300, 100)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        self.name_edit = QLineEdit()
        form_layout.addRow("Nome:", self.name_edit)

        if self.directory_id:
            # Carrega dados do diretório para edição
            try:
                with obter_conexao() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT name, parent_id
                          FROM directories
                         WHERE id = ?
                    """, (self.directory_id,))
                    row = cursor.fetchone()
                if row:
                    self.name_edit.setText(row[0])
                    self.parent_directory_id = row[1]
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar diretório: {e}")

        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.salvar)
        btn_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

    def salvar(self):
        nome = self.name_edit.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome do diretório não pode ser vazio.")
            return
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                if self.directory_id:
                    cursor.execute("""
                        UPDATE directories
                           SET name = ?
                         WHERE id = ?
                    """, (nome, self.directory_id))
                else:
                    cursor.execute("""
                        INSERT INTO directories (name, parent_id)
                        VALUES (?, ?)
                    """, (nome, self.parent_directory_id))
                conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar diretório: {e}")
