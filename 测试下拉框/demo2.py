import sys
from qtpy.QtWidgets import QMainWindow, QPushButton, QApplication


class First(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
    def closewin(self):
        self.close()

    def initUI(self):
        self.btn = QPushButton("Button", self)
        self.btn.move(30, 50)

        self.setGeometry(300, 300, 500, 500)
        self.setWindowTitle('修改文件列表')
        self.show()

class Second(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 290, 150)
        self.setWindowTitle('Get sender')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    a = First()
    b = Second()
    a.show()
    a.btn.clicked.connect(a.closewin)
    a.btn.clicked.connect(b.show)
    sys.exit(app.exec_())