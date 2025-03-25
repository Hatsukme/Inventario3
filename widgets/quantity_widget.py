from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QMessageBox
from database import obter_conexao


class QuantityWidget(QWidget):
    """
    Widget customizado que exibe a quantidade de um item
    e permite incrementá-la ou decrementá-la diretamente na tabela.
    """

    def __init__(self, item_id, quantity, parent=None):
        super().__init__(parent)
        self.item_id = item_id

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.btn_decrease = QPushButton("-")
        self.btn_decrease.setFixedWidth(20)
        self.label = QLabel(str(quantity))
        self.label.setFixedWidth(30)
        self.label.setAlignment(Qt.AlignCenter)
        self.btn_increase = QPushButton("+")
        self.btn_increase.setFixedWidth(20)

        self.layout.addWidget(self.btn_decrease)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn_increase)

        # Conecta os cliques aos métodos de incremento/decremento
        self.btn_increase.clicked.connect(self.increase)
        self.btn_decrease.clicked.connect(self.decrease)

    def update_quantity_in_db(self, new_quantity):
        try:
            with obter_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE items SET quantity = ? WHERE id = ?",
                    (new_quantity, self.item_id)
                )
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar quantidade: {e}")

    def increase(self):
        new_quantity = int(self.label.text()) + 1
        self.label.setText(str(new_quantity))
        self.update_quantity_in_db(new_quantity)

    def decrease(self):
        current = int(self.label.text())
        if current > 0:
            new_quantity = current - 1
            self.label.setText(str(new_quantity))
            self.update_quantity_in_db(new_quantity)
