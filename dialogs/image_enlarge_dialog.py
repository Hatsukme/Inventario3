import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPixmap

from widgets.zoomable_label import ZoomableLabel

class ImageEnlargeDialog(QDialog):
    """
    Diálogo que mostra a imagem em tamanho ampliado,
    permitindo zoom via roda do mouse (com Ctrl pressionado) e arrasto.
    """
    def __init__(self, parent=None, image_path=None):
        super().__init__(parent)
        self.setWindowTitle("Imagem Ampliada")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.resize(800, 600)
        self.image_path = image_path
        self.scaleFactor = 1.0
        self.zoom_min = 0.25
        self.zoom_max = 2.0

        layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.label = ZoomableLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.label)

        if self.image_path and os.path.exists(self.image_path):
            self.refresh_images()

        self.scroll_area.viewport().installEventFilter(self)

    def refresh_images(self):
        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            new_width = max(1, int(pixmap.width() * self.scaleFactor))
            new_height = max(1, int(pixmap.height() * self.scaleFactor))
            new_size = pixmap.size().scaled(new_width, new_height, Qt.KeepAspectRatio)
            transform_mode = (Qt.FastTransformation if self.scaleFactor < 1.0
                              else Qt.SmoothTransformation)
            scaled_pixmap = pixmap.scaled(new_size, Qt.KeepAspectRatio, transform_mode)
            self.label.setPixmap(scaled_pixmap)
            self.label.resize(scaled_pixmap.size())

    def eventFilter(self, source, event):
        if event.type() == QEvent.Wheel and source is self.scroll_area.viewport():
            # Zoom com Ctrl + roda do mouse
            if event.modifiers() == Qt.ControlModifier:
                delta = event.angleDelta().y()
                new_scale = self.scaleFactor * (1.25 if delta > 0 else 0.8)
                new_scale = min(max(new_scale, self.zoom_min), self.zoom_max)
                if new_scale != self.scaleFactor:
                    self.scaleFactor = new_scale
                    self.refresh_images()
                return True
        return super().eventFilter(source, event)
