from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon

def colorize_icon(png_path, color):
    pixmap = QPixmap(png_path)
    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(colored_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), QColor(color))
    painter.end()

    return QIcon(colored_pixmap)