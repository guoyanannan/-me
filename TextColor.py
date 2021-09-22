import sys
from qtpy.QtWidgets import *
from qtpy.QtCore    import *
from qtpy.QtGui     import *


qss = """

QMenuBar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 lightgray, stop:1 darkgray);
}
QMenuBar::item {
    spacing: 3px;
    padding: 2px 10px;
    background-color: rgb(0,0,0);
    color: rgb(255,255,255);
    border-radius: 5px;
}
QMenuBar::item:selected {
    background-color: rgb(244,164,96);
}
QMenuBar::item:pressed {
    background: rgb(128,0,0);
}

/* +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ */

QMenu {
    background-color: #ABABAB;
    border: 1px solid black;
    margin: 2px;
}
QMenu::item {
    background-color: transparent;
}
QMenu::item:selected {
    background-color: #654321;
    color: rgb(255,255,255);
}
"""


class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

### vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        mainMenu = self.menuBar()
        testMenu = mainMenu.addMenu('mainMenu')


        mainMenu1 = self.menuBar()
        #mainMenu1.setStyleSheet(qss)

        testMenu1 = mainMenu1.addMenu('mainMenu1')
        mainMenu.setStyleSheet(qss)
        testMenu2 = mainMenu1.addMenu('mainMenu2')

        test1_dropButton = QAction('Test 1', self)
        testMenu.addAction(test1_dropButton)

        test2_dropButton = QAction('Test 2', self)
        test2_dropButton.triggered.connect(self.displayImage)
        testMenu.addAction(test2_dropButton)

        test_dropButton = QAction('Exit', self)
        # test_dropButton.setShortcut('Ctrl+E')
        test_dropButton.triggered.connect(self.close)
        testMenu.addAction(test_dropButton)
### ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layV = QVBoxLayout(central_widget)

    def displayImage(self):
        # pixmap = QPixmap("D:/_Qt/img/pyqt.jpg")
        pixmap = QPixmap("")
        lbl = QLabel(self)
        self.layV.addWidget(lbl)
        lbl.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))


if __name__ == '__main__':
    app = QApplication([str])

    # app.setStyleSheet(qss)         # <

    ex = Example()
    ex.setWindowTitle('TestOne')
    #ex.setWindowIcon(QIcon('D:/_Qt/img/py-qt.png'))
    ex.resize(420,440)
    ex.show()
    sys.exit(app.exec_())