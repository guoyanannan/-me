from qtpy import QtGui
from qtpy.QtWidgets import QMessageBox


def info_box(value, title='标注工具[测试版本v1.0.0]:BKVISION', widget=None, delay=1.5):

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