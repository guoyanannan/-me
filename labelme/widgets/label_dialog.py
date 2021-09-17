import re

from qtpy import QT_VERSION
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from labelme.logger import logger
import labelme.utils


QT5 = QT_VERSION[0] == "5"


# TODO(unknown):
# - Calculate optimal position so as not to go out of screen area.


class LabelQLineEdit(QtWidgets.QLineEdit):
    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)


class LabelDialog(QtWidgets.QDialog):
    def __init__(
        self,
        # # text="Enter object label",
        # text="请输入缺陷类别名<英文或拼音,必填项!!!!!!>",
        # text1='请输入中文类别名,选填',
        # text2='请输入缺陷的置信度,选填,<范围1至9,值越大确认度越高>',
        # text3='请输入缺陷的清晰度,选填,<范围1至9,值越大清晰度越高>',
        # text4='请输入整幅图的清晰度,选填,<范围1至9,值越大清晰度越高>',
        # # text3='请输入整幅图的清晰度,选填,<范围1至9,值越大清晰度越高>',
        # # text4='请输入缺陷的清晰度,选填,<范围1至9,值越大清晰度越高>',

        parent=None,
        labels=None,
        sort_labels=True,
        show_text_field=True,
        completion="startswith",
        fit_to_content=None,
        flags=None,
        EngClsList=[],
        ChiClsList=[],
    ):

        if fit_to_content is None:
            fit_to_content = {"row": False, "column": True}
        #fit_to_content = {"row": True, "column": False}
        self._fit_to_content = fit_to_content

        super(LabelDialog, self).__init__(parent)
        #
        self.eng_list = EngClsList
        self.chi_list = ChiClsList
        # 实例化QComBox对象->英文类别
        self.cb = QtWidgets.QComboBox()
        # 单个条目
        # self.cb.addItems(['cls1','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3','cls2','cls3'])
        self.cb.addItems(self.eng_list)
        self.cb.currentIndexChanged.connect(self.postProcess)
        self.cb.activated.connect(lambda: self.to_comboBox_2(self.cb.currentText()))

        #
        # 实例化QComBox对象->中文类别
        self.cb1 = QtWidgets.QComboBox()
        # 单个条目
        # self.cb1.addItems(['类别1', '类别2', '类别3'])
        self.cb1.addItems(self.chi_list)
        self.cb1.currentIndexChanged.connect(self.postProcess)
        self.cb1.activated.connect(lambda: self.to_comboBox_1(self.cb1.currentText()))
        #
        # 实例化QComBox对象->缺陷置信度
        self.cb2 = QtWidgets.QComboBox()
        # 单个条目
        self.cb2.addItems(['9', '8', '7','6','5','4','3','2','1'])
        self.cb2.currentIndexChanged.connect(self.postProcess)
        #
        # 实例化QComBox对象->缺陷清晰度
        self.cb3 = QtWidgets.QComboBox()
        # 单个条目
        self.cb3.addItems(['9', '8', '7','6','5','4','3','2','1'])
        self.cb3.currentIndexChanged.connect(self.postProcess)
        #
        # 实例化QComBox对象->整张图清晰度
        self.cb4 = QtWidgets.QComboBox()
        # 单个条目
        self.cb4.addItems(['9', '8', '7','6','5','4','3','2','1'])
        self.cb4.currentIndexChanged.connect(self.postProcess)

        #输入框
        self.edit = LabelQLineEdit()
        #self.edit.setPlaceholderText(text)
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)

        #
        self.edit1 = LabelQLineEdit()
        #self.edit1.setPlaceholderText(text1)
        self.edit1.setValidator(labelme.utils.labelValidator())
        self.edit1.editingFinished.connect(self.postProcess)
        #
        self.edit2 = LabelQLineEdit()
        #self.edit2.setPlaceholderText(text2)
        self.edit2.setValidator(labelme.utils.labelValidator())
        self.edit2.editingFinished.connect(self.postProcess_three)
        #
        self.edit3 = LabelQLineEdit()
        #self.edit3.setPlaceholderText(text3)
        self.edit3.setValidator(labelme.utils.labelValidator())
        self.edit3.editingFinished.connect(self.postProcess_three)
        #
        self.edit4 = LabelQLineEdit()
        #self.edit4.setPlaceholderText(text4)
        self.edit4.setValidator(labelme.utils.labelValidator())
        self.edit4.editingFinished.connect(self.postProcess_three)
        if flags:
            print('flags:',flags)
            self.edit.textChanged.connect(self.updateFlags)
        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setPlaceholderText("Group ID,选填项,用于分组！！！")
        self.edit_group_id.setValidator(
            QtGui.QRegExpValidator(QtCore.QRegExp(r"\d*"), None)
        )
        layout = QtWidgets.QVBoxLayout()

        if show_text_field:
            layout_1 = QtWidgets.QHBoxLayout()
            #原始文本框
            layout_edit_t = QtWidgets.QVBoxLayout()
            self.edit.setFixedHeight(20)
            self.edit1.setFixedHeight(20)
            self.edit2.setFixedHeight(20)
            self.edit3.setFixedHeight(20)
            self.edit4.setFixedHeight(20)
            layout_edit_t.addWidget(self.edit, 2)
            layout_edit_t.addWidget(self.edit1, 2)
            layout_edit_t.addWidget(self.edit2, 2)
            layout_edit_t.addWidget(self.edit3, 2)
            layout_edit_t.addWidget(self.edit4, 2)
            # layout_edit.addWidget(self.edit_group_id, 2)


            '''
            #下拉框
            # layout_edit.addWidget(self.cb, 2)
            layout.addLayout(layout_edit)
            '''
            #下拉框
            layout_edit = QtWidgets.QFormLayout()
            # layout_edit.addWidget(self.edit)
            # layout_edit.addWidget(self.edit1)
            # layout_edit.addWidget(self.edit2)
            # layout_edit.addWidget(self.edit3)
            # layout_edit.addWidget(self.edit4)
            # layout_edit.addWidget(self.edit_group_id)
            # 下拉框
            # layout_edit.addWidget(self.cb)
            layout_edit.addRow("英文类别名：",self.cb)
            layout_edit.addRow("中文类别名：",self.cb1)
            layout_edit.addRow("缺陷置信度：",self.cb2)
            layout_edit.addRow("缺陷清晰度：",self.cb3)
            layout_edit.addRow("整图清晰度：",self.cb4)
            layout_1.addLayout(layout_edit)
            layout_1.addLayout(layout_edit_t)
            layout.addLayout(layout_1)
        # buttons
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        #设置图标
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon("done"))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon("undo"))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        # label_list
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content["row"]:
            self.labelList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content["column"]:
            self.labelList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        self._sort_labels = sort_labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove
            )
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.labelList.itemDoubleClicked.connect(self.labelDoubleClicked)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList)
        # label_flags
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        layout.addItem(self.flagsLayout)
        self.edit.textChanged.connect(self.updateFlags)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != "startswith":
            logger.warn(
                "completion other than 'startswith' is only "
                "supported with Qt5. Using 'startswith'"
            )
            completion = "startswith"
        if completion == "startswith":
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == "contains":
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError("Unsupported completion: {}".format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        self.edit.setText(item.text())

    def to_comboBox_2(self, text):
        self.cb1.setCurrentText(self.chi_list[self.eng_list.index(text)])

    def to_comboBox_1(self, text):
        self.cb.setCurrentText(self.eng_list[self.chi_list.index(text)])

    def validate(self):
        # text = self.edit.text()
        text = self.cb.currentText()
        if hasattr(text, "strip"):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def labelDoubleClicked(self, item):
        self.validate()

    def postProcess_three(self):
        #print('进入postProcess_three函数')
        list_cb = [self.cb2,self.cb3,self.cb4,]
        list_edit = [self.edit2,self.edit3,self.edit4]
        for i in range(len(list_edit)):
            op_e = list_edit[i]
            if op_e.text():
                text = op_e.text()
                if hasattr(text, "strip"):
                    text = text.strip()
                else:
                    text = text.trimmed()
                if text in ['9', '8', '7','6','5','4','3','2','1']:
                    op_e.setText(text)
                    list_cb[i].setCurrentText(text)
                else:
                    op_e.setText('')
                    QtWidgets.QMessageBox.warning(self, '错误', f"{text}不在范围1-9之内,请重新输入，否则默认左边值！！！！", )


    def postProcess(self):
        #print('进入postProcess函数')
        #print(str(self.edit.text()))
        if str(self.edit.text()):
            text = self.edit.text()
            if hasattr(text, "strip"):
                text = text.strip()
            else:
                text = text.trimmed()
            if text in self.eng_list:
                chi_text = self.chi_list[self.eng_list.index(text)]
                self.edit.setText(text)
                self.edit.setSelection(0, len(text))
                self.edit1.setText(chi_text)
                self.edit1.setSelection(0, len(chi_text))
                self.cb.setCurrentText(text)
                self.cb1.setCurrentText(chi_text)
            else:
                self.edit.setText('')
                self.edit1.setText('')
                QtWidgets.QMessageBox.warning(self, '错误', f"{text}不是定义的类别，请重新输入！！！", )
                return
                # text = self.cb.currentText()
                # if hasattr(text, "strip"):
                #     text = text.strip()
                # else:
                #     text = text.trimmed()


        else:
            if self.edit1.text():
                if self.edit1.text() in self.chi_list:
                    text1 = self.edit1.text()
                    text = self.eng_list[self.chi_list.index(text1)]
                    self.edit1.setText(text1)
                    self.edit.setText(text)
                    self.cb.setCurrentText(text)
                    self.cb1.setCurrentText(text1)
                else:
                    self.edit1.setText('')
                    QtWidgets.QMessageBox.warning(self, '错误', f"{self.edit1.text()}不是定义的类别！！！", )

            else:
                text = self.cb.currentText()
                if hasattr(text, "strip"):
                    text = text.strip()
                else:
                    text = text.trimmed()
                self.cb.setCurrentText(text)
        # text = self.edit.text()
        #text = self.cb.currentText()
        #print('复合框：',text)
        # if hasattr(text, "strip"):
        #     text = text.strip()
        # else:
        #     text = text.trimmed()
        # self.edit.setText(text)
        # self.cb.setCurrentText(text)
        #print('是否添加成功耶：',bool(self.cb.setCurrentText(text)))

    def updateFlags(self, label_new):
        # keep state of shared flags
        flags_old = self.getFlags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(None)

    def resetFlags(self, label=""):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            flags[item.text()] = item.isChecked()
        return flags

    def getGroupId(self):
        group_id = self.edit_group_id.text()
        if group_id:
            return int(group_id)
        return None

    def popUp(self, text=None, move=True, flags=None, group_id=None,text_ch=None,text_dif=None,text_imgdif=None,text_objdif=None,):
        if self._fit_to_content["row"]:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content["column"]:
            self.labelList.setMinimumWidth(
                self.labelList.sizeHintForColumn(0) + 2
            )
        # if text is None, the previous label in self.edit is kept
        if text is None:
            # print('text是None时text的值:', text)
            '''
            #origin
            text = self.edit.text()
            text1 = self.edit1.text()
            text2 = self.edit2.text()
            text3 = self.edit3.text()
            text4 = self.edit4.text()
            '''
            #is_use_edit = False
            #编辑框设置图像清晰度等默认值
            self.edit.setText('')
            self.edit1.setText('')
            self.edit2.setText('9')
            self.edit3.setText('9')
            self.edit4.setText('9')
            #下拉框
            text = self.cb.currentText()
            text1 = self.cb1.currentText()
            text2 = self.cb2.currentText()
            text3 = self.cb3.currentText()
            text4 = self.cb4.currentText()
            #print('text是None时text01234的值:',text,text1,text2,text3,text4)

        else:
            # print('text非空时:')
            '''
            text = text
            text1 = text_ch
            text2 = text_dif
            text3 = text_objdif
            text4 = text_imgdif
            # 下拉框
            text5 = self.cb.currentText()
            print("下拉框选择值》》》", text5)
            '''
            # #下拉框
            # text = text
            # text1 = text_ch
            # text2 = text_dif
            # text3 = text_objdif
            # text4 = text_imgdif
            #is_use_edit = True

            text = self.edit.text()
            # print('text:',text)
            if text:
                text1 = self.edit1.text()
                text2 = self.edit2.text()
                text3 = self.edit3.text()
                text4 = self.edit4.text()
                self.edit.setText('')
                self.edit1.setText('')
                #print(text, text1, text2, text3, text4)
            else:
                #is_use_edit = False
                self.edit.setText('')
                self.edit1.setText('')
                self.edit2.setText('9')
                self.edit3.setText('9')
                self.edit4.setText('9')
                #print('info：',self.edit.text(),self.edit1.text(),self.edit2.text(),self.edit3.text(),self.edit4.text(),)



        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)
        # if True:
        #     print('进入文本框赋值!!')
        #     self.edit.setText(text)
        #     self.edit.setSelection(0, len(text))
        #     #Chinese
        #     self.edit1.setText(str(text1))
        #     #self.edit1.setSelection(0, len(text1))
        #     #difficult
        #     self.edit2.setText(str(text2))
        #     #self.edit2.setSelection(0, len(text2))
        #     #definition
        #     self.edit3.setText(str(text3))
        #     self.edit4.setText(str(text4))
        #     #self.edit3.setSelection(0, len(text3))
        #     if group_id is None:
        #         self.edit_group_id.clear()
        #     else:
        #         self.edit_group_id.setText(str(group_id))

        # items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        items = False
        if items:
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)
        if move:
            self.move(QtGui.QCursor.pos())
        if self.exec_():
            '''
            #oringin
            text4 = self.edit4.text()
            text3 = self.edit3.text()
            text2 = self.edit2.text()
            if len(text4)==0:
                text4 = '9'
            if len(text3)==0:
                text3 = '9'
            if len(text2)==0:
                text2 = '9'
            
            
            #text, flags, group_id,text_ch,text_dif,text_imgdif
            return self.edit.text(), self.getFlags(), self.getGroupId(),self.edit1.text(),text2,text3,text4
            '''
            # print("执行情况下英文名|标签|组|中文名|缺陷置信度|缺陷清晰度|整图清晰度|:")
            # print(self.cb.currentText(), self.getFlags(), self.getGroupId(), self.cb1.currentText(), self.cb2.currentText(), self.cb3.currentText(), self.cb4.currentText())
            return self.cb.currentText(), self.getFlags(), self.getGroupId(), self.cb1.currentText(), self.cb2.currentText(), self.cb3.currentText(), self.cb4.currentText()
        else:
            return None, None, None,None, None, None,None
