from qtpy import QtCore, QtGui, QtWidgets
from labelme.utils import newIcon
from labelme import __appname__
import sys


app = QtWidgets.QApplication(sys.argv)
app.setApplicationName(__appname__)
app.setWindowIcon(newIcon("icon"))
# # infoBox = QtWidgets.QMessageBox.warning(QtWidgets.QMainWindow(), '错误', f"网络异常,请检查当前目录{os.getcwd()}")
# # infoBox.setStandardButtons(QtWidgets.QMessageBox.Ok )
# # infoBox.button(QtWidgets.QMessageBox.Ok).animateClick(1*1000)       #3秒自动关闭
# # infoBox.exec_()
# infoBox = QtWidgets.QMessageBox()
# infoBox.setIcon(QtWidgets.QMessageBox.Information)
# infoBox.setText("保存完成！")
# infoBox.setWindowTitle("Information")
# infoBox.setStandardButtons(QtWidgets.QMessageBox.Ok )
# infoBox.button(QtWidgets.QMessageBox.Ok).animateClick(3*1000)       #3秒自动关闭
# infoBox.exec_()

def info_box(value, title='信息', widget=None, delay=1.5):
    from qtpy.QtWidgets import QMessageBox
    """
    消息盒子
    :param value: 显示的信息内容
    :param title: 弹窗的标题
    :param widget: 父窗口
    :param delay: 弹窗默认关闭时间， 单位：秒
    """
    msgBox = QMessageBox(parent=widget)
    # 设置默认 ICON
    # msgBox.setWindowIcon(QtGui.QIcon('./default.ico'))

    # 设置信息内容使用字体
    font = QtGui.QFont()
    font.setFamily("微软雅黑")
    font.setPointSize(10)
    font.setBold(True)
    font.setWeight(30)
    msgBox.setFont(font)

    msgBox.setWindowTitle(title)
    msgBox.setText(value)
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.setDefaultButton(QMessageBox.Ok)
    # 设置 QMessageBox 自动关闭时长
    msgBox.button(QMessageBox.Ok).animateClick(1000 * delay)
    msgBox.exec()
    print(11111)

if __name__ == '__main__':
    info_box(value='检查更新中......')