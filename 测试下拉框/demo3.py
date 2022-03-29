'''
动态显示当前时间
QTimer：如果完成周期性任务可以使用这个
QThread：如果完成单个任务可以使用这个
多线程：用于同时完成多个任务
'''
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
class Activetime(QWidget):
    #初始化
    def __init__(self):
        super(Activetime, self).__init__()
        self.initUI()
    def initUI(self):
        self.setWindowTitle("动态显示时间")
        self.resize(200,100)

        self.lable=QLabel("显示当前时间")
        self.button1=QPushButton("开始时间")
        self.button2=QPushButton("结束")
        #设置网格布局
        layout=QGridLayout()

        self.timer=QTimer()
        self.timer.timeout.connect(lambda:self.showtime())#这个通过调用槽函数来刷新时间
        self.timer.start()
        layout.addWidget(self.lable,0,0,1,2)
        # layout.addWidget(self.button1,1,0)
        # layout.addWidget(self.button2,1,1)
        # self.timer.timeout.connect(self.starttimer)
        # self.button1.clicked.connect(self.starttimer)
        # self.button2.clicked.connect(self.endtimer)
        self.setLayout(layout)


    def showtime(self):
        time=QDateTime.currentDateTime()#获取当前时间
        timedisplay=time.toString("yyyy-MM-dd hh:mm:ss")#格式化一下时间
        print(timedisplay)
        self.lable.setText(timedisplay)
        # self.starttimer()

    def starttimer(self):
        self.timer.start(1000)#每隔一秒刷新一次，这里设置为1000ms
        # self.button1.setEnabled(False)
        # self.button2.setEnabled(True)

    def endtimer(self):
        self.timer.stop()
        # self.button1.setEnabled(True)
        # self.button2.setEnabled(False)

if __name__=="__main__":
    app=QApplication(sys.argv)
    main=Activetime()
    main.show()
    sys.exit(app.exec_())
