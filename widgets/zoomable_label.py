from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QEvent

class ZoomableLabel(QLabel):
    """
    Label que permite zoom e "arrastar" a imagem dentro de um QScrollArea.
    É usada dentro do diálogo de imagem ampliada.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._dragStartPos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._dragStartPos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.pos() - self._dragStartPos
            scroll_area = self.parentWidget()
            while scroll_area and not hasattr(scroll_area, "horizontalScrollBar"):
                scroll_area = scroll_area.parentWidget()
            if scroll_area and hasattr(scroll_area, "horizontalScrollBar"):
                hbar = scroll_area.horizontalScrollBar()
                vbar = scroll_area.verticalScrollBar()
                hbar.setValue(hbar.value() - delta.x())
                vbar.setValue(vbar.value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        super().mouseReleaseEvent(event)
