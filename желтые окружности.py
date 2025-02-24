import sys

from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget, QApplication, QMainWindow, QPushButton
from random import randint
from PyQt6 import uic


class Suprematism(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('желтые окружности.ui', self)  # Загружаем дизайн
        self.initUI()

    def initUI(self):
        self.coords = []  # координаты мышки
        self.do_paint = False
        self.pushButton.clicked.connect(self.timer_start)

    # self.pushButton = QPushButton()

    def paintEvent(self, event):
        if self.do_paint:
            qp = QPainter(self)
            qp.setBrush(QColor(255, 255, 0))
            qp.begin(self)
            self.figure(qp)
            qp.end()
        self.do_paint = False

    def timer_start(self):
        self.t = QTimer(self)
        self.t.timeout.connect(self.paint)
        self.t.start(1000)
        self.pushButton.setDisabled(True)

    def paint(self):
        if len(self.coords) > 9:
            self.coords = self.coords[1:]
        self.do_paint = True
        x, y = randint(0, self.size().width()), randint(0, self.size().height())
        self.coords.append((x, y))
        self.update()

    def figure(self, qp):
        for coord in self.coords:
            r = randint(10, 40)
            qp.drawEllipse(QPointF(*coord), r, r)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Suprematism()
    ex.show()
    sys.exit(app.exec())