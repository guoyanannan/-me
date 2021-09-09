import sys
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *

class ComboxDemo(QWidget):
  def __init__(self,parent=None):
    super(ComboxDemo, self).__init__(parent)
    #设置标题
    self.setWindowTitle('ComBox例子')
    #设置初始界面大小
    self.resize(300,90)
    self.one_list = ['Java','C#','PHP']
    self.two_list = ['爪哇','冲刷配','度弧度']
    #垂直布局
    # layout=QVBoxLayout()
    layout=QFormLayout()
    #水平布局
    #创建标签，默认空白
    self.btn1=QLabel('')
    #self.btn2=QLabel('编程语言:')

    #实例化QComBox对象
    self.cb=QComboBox()
    self.cb1=QComboBox()
    #单个添加条目
    # self.cb1.addItem('C')
    # self.cb1.addItem('C++')
    # self.cb1.addItem('Python')
    #多个添加条目
    self.cb.addItems(self.one_list)
    #当下拉索引发生改变时发射信号触发绑定的事件
    # self.cb.currentIndexChanged.connect(self.selectionchange)
    self.cb.activated.connect(lambda :self.to_comboBox_2(self.cb.currentText()))
    self.cb1.addItems(self.two_list)
    #控件添加到布局中，设置布局

    layout.addRow("哈哈：",self.cb)
    layout.addRow("呵呵：",self.cb1)
    # layout.addRow(self.cb)
    # layout.addWidget(self.btn1)
    # layout.addRow(self.btn1)
    self.setLayout(layout)

  # def selectionchange(self,i):
  #   #标签用来显示选中的文本
  #   #currentText()：返回选中选项的文本
  #   self.btn1.setText(self.cb.currentText())
  #   print('Items in the list are:')
  #   #输出选项集合中每个选项的索引与对应的内容
  #   #count()：返回选项集合中的数目
  #   for count in range(self.cb.count()):
  #     print('Item'+str(count)+'='+self.cb.itemText(count))
  #     print('current index',i,'selection changed',self.cb.currentText())
  def to_comboBox_2(self,text):
      # print(text)
      # print(self.one_list.index(text))
      self.cb1.setCurrentText(self.two_list[self.one_list.index(text)])

if __name__ == '__main__':
  app=QApplication(sys.argv)
  comboxDemo=ComboxDemo()
  comboxDemo.show()
  sys.exit(app.exec_())