from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QColorDialog, QHBoxLayout


class NoteDialog(QDialog):
    def __init__(self, current_note="", current_color=""):
        super().__init__()
        self.setWindowTitle("Note")
        self.resize(300, 200)
        self.note = current_note
        self.color = current_color

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter your note:"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(current_note)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.btn_color = QPushButton("Choose Color")
        self.btn_color.clicked.connect(self.choose_color)
        btn_layout.addWidget(self.btn_color)
        self.lbl_color = QLabel("No color" if not current_color else current_color)
        btn_layout.addWidget(self.lbl_color)
        layout.addLayout(btn_layout)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()
            self.lbl_color.setText(self.color)

    def get_note_data(self):
        return self.text_edit.toPlainText(), self.color
