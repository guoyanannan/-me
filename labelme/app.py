# -*- coding: utf-8 -*-

import functools
import math
import os
import os.path as osp
import re
import webbrowser

import imgviz
import qtpy.QtWidgets
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from labelme import __appname__
from labelme import PY2
from labelme import QT5

from . import utils
from labelme.config import get_config
from labelme.label_file import LabelFile
from labelme.label_file import LabelFileError
from labelme.logger import logger
from labelme.shape import Shape
from labelme.widgets import BrightnessContrastDialog
from labelme.widgets import Canvas
from labelme.widgets import LabelDialog
from labelme.widgets import LabelListWidget
from labelme.widgets import LabelListWidgetItem
from labelme.widgets import ToolBar
from labelme.widgets import UniqueLabelQListWidget
from labelme.widgets import ZoomWidget


# FIXME
# - [medium] Set max zoom value to something big enough for FitWidth/Window

# TODO(unknown):
# - [high] Add polygon movement with arrow keys
# - [high] Deselect shape when clicking and already selected(?)
# - [low,maybe] Preview images on file dialogs.
# - Zoom is too "steppy".


LABEL_COLORMAP = imgviz.label_colormap(value=200)


class MainWindow(QtWidgets.QMainWindow):

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2

    def __init__(
        self,
        config=None,
        filename=None,
        output=None,
        output_file=None,
        output_dir=None,
        mode = 1,
    ):
        self.mode =mode
        self.childSSS = select_product_type(self.getClsNameLZ_win,self.getClsNameRZ_win,self.getClsNameBC_win,self.getClsNameCB_win,self.getClsNameZP_win,self.getClsNameZF_win)
        self.select_op = False
        self.ch_name = None
        self.EngClsOri = ['BeiJing','0','1','2','3','4','5','6','7','8','9',
                          'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                          'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                          '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                          'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                          'u','v','w','x','y','z']
        self.ChiClsOri = ['背景','0','1','2','3','4','5','6','7','8','9',
                          'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                          'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                          '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                          'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                          'u','v','w','x','y','z']
        if output is not None:
            logger.warning(
                "argument output is deprecated, use output_file instead"
            )
            if output_file is None:
                output_file = output

        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config

        # set default shape colors
        Shape.line_color = QtGui.QColor(*self._config["shape"]["line_color"])
        Shape.fill_color = QtGui.QColor(*self._config["shape"]["fill_color"])
        Shape.select_line_color = QtGui.QColor(
            *self._config["shape"]["select_line_color"]
        )
        Shape.select_fill_color = QtGui.QColor(
            *self._config["shape"]["select_fill_color"]
        )
        Shape.vertex_fill_color = QtGui.QColor(
            *self._config["shape"]["vertex_fill_color"]
        )
        Shape.hvertex_fill_color = QtGui.QColor(
            *self._config["shape"]["hvertex_fill_color"]
        )

        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)

        # Whether we need to save or not.
        self.dirty = False

        self._noSelectionSlot = False

        # Main widgets and related state.
        self.labelDialog = LabelDialog(
            parent=self,
            labels=self._config["labels"],
            sort_labels=self._config["sort_labels"],
            show_text_field=self._config["show_label_text_field"],
            completion=self._config["label_completion"],
            fit_to_content=self._config["fit_to_content"],
            flags=self._config["label_flags"],
            EngClsList = self.EngClsOri,
            ChiClsList = self.ChiClsOri,
        )

        self.labelList = LabelListWidget()
        self.lastOpenDir = None

        TB = QtWidgets.QToolBar('类别名2')
        self.ses = QtWidgets.QComboBox()
        self.ses.addItems(['1','2'])
        # self.ses.currentIndexChanged.connect(self.postProcess)
        layout_s = QtWidgets.QFormLayout()
        layout_s.addRow("类别名：", self.ses)
        TB.addWidget(self.ses)
        TB.addSeparator()



        self.flag_dock = self.flag_widget = None
        # self.flag_dock = QtWidgets.QDockWidget(self.tr("Flags"), self)
        self.flag_dock = QtWidgets.QDockWidget(self.tr("标记"), self)
        self.flag_dock.setObjectName("Flags")
        self.flag_widget = QtWidgets.QListWidget()
        if config["flags"]:
            self.loadFlags({k: False for k in config["flags"]})
        self.flag_dock.setWidget(self.flag_widget)
        self.flag_widget.itemChanged.connect(self.setDirty)
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.labelList.itemDoubleClicked.connect(self.editLabel)
        self.labelList.itemChanged.connect(self.labelItemChanged)
        self.labelList.itemDropped.connect(self.labelOrderChanged)
        self.shape_dock = QtWidgets.QDockWidget(
            # self.tr("Polygon Labels"), self
            self.tr("多边形标签"), self
        )
        self.shape_dock.setObjectName("Labels")
        # print('进入8')
        self.shape_dock.setWidget(self.labelList)

        self.uniqLabelList = UniqueLabelQListWidget()
        self.uniqLabelList.setToolTip(
            self.tr(
                "Select label to start annotating for it. "
                "Press 'Esc' to deselect."
            )
        )
        if self._config["labels"]:
            for label in self._config["labels"]:
                item = self.uniqLabelList.createItemFromLabel(label)
                self.uniqLabelList.addItem(item)
                rgb = self._get_rgb_by_label(label)
                self.uniqLabelList.setItemLabel(item, label, rgb)
        # self.label_dock = QtWidgets.QDockWidget(self.tr(u"Label List"), self)
        self.label_dock = QtWidgets.QDockWidget(self.tr(u"标签列表"), self)
        self.label_dock.setObjectName(u"Label List")
        self.label_dock.setWidget(self.uniqLabelList)

        self.fileSearch = QtWidgets.QLineEdit()
        # self.fileSearch.setPlaceholderText(self.tr("Search Filename"))
        self.fileSearch.setPlaceholderText(self.tr("按文件名检索"))
        self.fileSearch.textChanged.connect(self.fileSearchChanged)
        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(
            self.fileSelectionChanged
        )
        fileListLayout = QtWidgets.QVBoxLayout()
        fileListLayout.setContentsMargins(0, 0, 0, 0)
        fileListLayout.setSpacing(0)
        fileListLayout.addWidget(self.fileSearch)
        fileListLayout.addWidget(self.fileListWidget)
        # self.file_dock = QtWidgets.QDockWidget(self.tr(u"File List"), self)
        self.file_dock = QtWidgets.QDockWidget(self.tr(u"文件列表"), self)
        self.file_dock.setObjectName(u"Files")
        fileListWidget = QtWidgets.QWidget()
        fileListWidget.setLayout(fileListLayout)
        self.file_dock.setWidget(fileListWidget)

        self.zoomWidget = ZoomWidget()
        self.setAcceptDrops(True)
        # print('进入9')
        self.canvas = self.labelList.canvas = Canvas(
            epsilon=self._config["epsilon"],
            double_click=self._config["canvas"]["double_click"],
            num_backups=self._config["canvas"]["num_backups"],
        )
        self.canvas.zoomRequest.connect(self.zoomRequest)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scrollArea.verticalScrollBar(),
            Qt.Horizontal: scrollArea.horizontalScrollBar(),
        }
        self.canvas.scrollRequest.connect(self.scrollRequest)

        self.canvas.newShape.connect(self.newShape)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)

        self.setCentralWidget(scrollArea)

        features = QtWidgets.QDockWidget.DockWidgetFeatures()
        for dock in ["flag_dock", "label_dock", "shape_dock", "file_dock"]:
            if self._config[dock]["closable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetClosable
            if self._config[dock]["floatable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetFloatable
            if self._config[dock]["movable"]:
                features = features | QtWidgets.QDockWidget.DockWidgetMovable
            getattr(self, dock).setFeatures(features)
            if self._config[dock]["show"] is False:
                getattr(self, dock).setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.flag_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.shape_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)

        # Actions
        action = functools.partial(utils.newAction, self)
        shortcuts = self._config["shortcuts"]
        quit = action(
            self.tr("&退出"),
            self.close,
            shortcuts["quit"],
            "quit",
            self.tr("Quit application"),
        )
        open_ = action(
            self.tr("&打开"),
            self.openFile,
            shortcuts["open"],
            "open",
            self.tr("Open image or label file"),
        )
        opendir = action(
            self.tr("&打开目录"),
            self.openDirDialog,
            shortcuts["open_dir"],
            "open",
            self.tr(u"Open Dir"),
        )
        openNextImg = action(
            self.tr("&下一幅"),
            self.openNextImg,
            shortcuts["open_next"],
            "next",
            self.tr(u"Open next (hold Ctl+Shift to copy labels)"),
            enabled=False,
        )
        openPrevImg = action(
            self.tr("&上一幅"),
            self.openPrevImg,
            shortcuts["open_prev"],
            "prev",
            self.tr(u"Open prev (hold Ctl+Shift to copy labels)"),
            enabled=False,
        )
        save = action(
            self.tr("&保存"),
            self.saveFile,
            shortcuts["save"],
            "save",
            self.tr("Save labels to file"),
            enabled=False,
        )
        saveAs = action(
            self.tr("&另存为"),
            self.saveFileAs,
            shortcuts["save_as"],
            "save-as",
            self.tr("Save labels to a different file"),
            enabled=False,
        )

        deleteFile = action(
            self.tr("&删除"),
            self.deleteFile,
            shortcuts["delete_file"],
            "delete",
            self.tr("Delete current label file"),
            enabled=False,
        )

        changeOutputDir = action(
            self.tr("&更改输出路径"),
            slot=self.changeOutputDirDialog,
            shortcut=shortcuts["save_to"],
            icon="open",
            tip=self.tr(u"Change where annotations are loaded/saved"),
        )

        saveAuto = action(
            text=self.tr("&自动保存"),
            slot=lambda x: self.actions.saveAuto.setChecked(x),
            icon="save",
            tip=self.tr("Save automatically"),
            checkable=True,
            enabled=True,
        )
        saveAuto.setChecked(self._config["auto_save"])


        saveWithImageData = action(
            # text="Save With Image Data",
            text="base64保存图像数据",
            slot=self.enableSaveImageWithData,
            tip="Save image data in label file",
            checkable=True,
            checked=self._config["store_data"],
        )

        close = action(
            # "&Close",
            "&关闭",
            self.closeFile,
            shortcuts["close"],
            "close",
            "Close current file",
        )

        toggle_keep_prev_mode = action(
            # self.tr("Keep Previous Annotation"),
            self.tr("保留最后的标注"),
            self.toggleKeepPrevMode,
            shortcuts["toggle_keep_prev_mode"],
            None,
            self.tr('Toggle "keep pevious annotation" mode'),
            checkable=True,
        )
        toggle_keep_prev_mode.setChecked(self._config["keep_prev"])

        createMode = action(
            # self.tr("Create Polygons"),
            self.tr("创建多边形"),
            lambda: self.toggleDrawMode(False, createMode="polygon"),
            shortcuts["create_polygon"],
            "objects",
            self.tr("Start drawing polygons"),
            enabled=False,
        )
        createRectangleMode = action(
            # self.tr("Create Rectangle"),
            self.tr("创建矩形"),
            lambda: self.toggleDrawMode(False, createMode="rectangle"),
            shortcuts["create_rectangle"],
            "objects",
            self.tr("Start drawing rectangles"),
            enabled=False,
        )
        createCircleMode = action(
            # self.tr("Create Circle"),
            self.tr("创建圆形"),
            lambda: self.toggleDrawMode(False, createMode="circle"),
            shortcuts["create_circle"],
            "objects",
            self.tr("Start drawing circles"),
            enabled=False,
        )
        createLineMode = action(
            # self.tr("Create Line"),
            self.tr("创建直线"),
            lambda: self.toggleDrawMode(False, createMode="line"),
            shortcuts["create_line"],
            "objects",
            self.tr("Start drawing lines"),
            enabled=False,
        )
        createPointMode = action(
            # self.tr("Create Point"),
            self.tr("创建控制点"),
            lambda: self.toggleDrawMode(False, createMode="point"),
            shortcuts["create_point"],
            "objects",
            self.tr("Start drawing points"),
            enabled=False,
        )
        createLineStripMode = action(
            # self.tr("Create LineStrip"),
            self.tr("创建折线"),
            lambda: self.toggleDrawMode(False, createMode="linestrip"),
            shortcuts["create_linestrip"],
            "objects",
            self.tr("Start drawing linestrip. Ctrl+LeftClick ends creation."),
            enabled=False,
        )
        editMode = action(
            self.tr("编辑多边形"),
            self.setEditMode,
            shortcuts["edit_polygon"],
            "edit",
            self.tr("Move and edit the selected polygons"),
            enabled=False,
        )

        delete = action(
            self.tr("删除多边形"),
            self.deleteSelectedShape,
            shortcuts["delete_polygon"],
            "cancel",
            self.tr("Delete the selected polygons"),
            enabled=False,
        )
        copy = action(
            # self.tr("Duplicate Polygons"),
            self.tr("复制多边形"),
            self.copySelectedShape,
            shortcuts["duplicate_polygon"],
            "copy",
            self.tr("Create a duplicate of the selected polygons"),
            enabled=False,
        )
        undoLastPoint = action(
            # self.tr("Undo last point"),
            self.tr("撤销最后的控制点"),
            self.canvas.undoLastPoint,
            shortcuts["undo_last_point"],
            "undo",
            self.tr("Undo last drawn point"),
            enabled=False,
        )
        addPointToEdge = action(
            # text=self.tr("Add Point to Edge"),
            text=self.tr("在边上加入控制点"),
            slot=self.canvas.addPointToEdge,
            shortcut=shortcuts["add_point_to_edge"],
            icon="edit",
            tip=self.tr("Add point to the nearest edge"),
            enabled=False,
        )
        removePoint = action(
            # text="Remove Selected Point",
            text="删除选定点",
            slot=self.removeSelectedPoint,
            icon="edit",
            tip="Remove selected point from polygon",
            enabled=False,
        )

        undo = action(
            # self.tr("Undo"),
            self.tr("&撤销"),
            self.undoShapeEdit,
            # None,
            shortcuts["undo"],
            "undo",
            self.tr("Undo last add and edit of shape"),
            enabled=False,
        )

        hideAll = action(
            # self.tr("&Hide\nPolygons"),
            self.tr("&隐藏多边形"),
            functools.partial(self.togglePolygons, False),
            icon="eye",
            tip=self.tr("Hide all polygons"),
            enabled=False,
        )
        showAll = action(
            # self.tr("&Show\nPolygons"),
            self.tr("&显示多边形"),
            functools.partial(self.togglePolygons, True),
            icon="eye",
            tip=self.tr("Show all polygons"),
            enabled=False,
        )

        help = action(
            # self.tr("&Tutorial"),
            self.tr("&教程"),
            self.tutorial,
            icon="help",
            tip=self.tr("Show tutorial page"),
        )

        zoom = QtWidgets.QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            self.tr(
                "Zoom in or out of the image. Also accessible with "
                "{} and {} from the canvas."
            ).format(
                utils.fmtShortcut(
                    "{},{}".format(shortcuts["zoom_in"], shortcuts["zoom_out"])
                ),
                utils.fmtShortcut(self.tr("Ctrl+Wheel")),
            )
        )
        self.zoomWidget.setEnabled(False)

        zoomIn = action(
            # self.tr("Zoom &In"),
            self.tr("&放大"),
            functools.partial(self.addZoom, 1.1),
            shortcuts["zoom_in"],
            "zoom-in",
            self.tr("Increase zoom level"),
            enabled=False,
        )
        zoomOut = action(
            # self.tr("&Zoom Out"),
            self.tr("&缩小"),
            functools.partial(self.addZoom, 0.9),
            shortcuts["zoom_out"],
            "zoom-out",
            self.tr("Decrease zoom level"),
            enabled=False,
        )
        zoomOrg = action(
            # self.tr("&Original size"),
            self.tr("&原始大小"),
            functools.partial(self.setZoom, 100),
            shortcuts["zoom_to_original"],
            "zoom",
            self.tr("Zoom to original size"),
            enabled=False,
        )
        fitWindow = action(
            # self.tr("&Fit Window"),
            self.tr("&适应窗口"),
            self.setFitWindow,
            shortcuts["fit_window"],
            "fit-window",
            self.tr("Zoom follows window size"),
            checkable=True,
            enabled=False,
        )
        fitWidth = action(
            # self.tr("Fit &Width"),
            self.tr("适应宽度"),
            self.setFitWidth,
            shortcuts["fit_width"],
            "fit-width",
            self.tr("Zoom follows window width"),
            checkable=True,
            enabled=False,
        )
        brightnessContrast = action(
            # "&Brightness Contrast",
            "&改变 亮度对比度",
            self.brightnessContrast,
            None,
            "color",
            "Adjust brightness and contrast",
            enabled=False,
        )
        # Group zoom controls into a list for easier toggling.
        zoomActions = (
            self.zoomWidget,
            zoomIn,
            zoomOut,
            zoomOrg,
            fitWindow,
            fitWidth,
        )
        self.zoomMode = self.FIT_WINDOW
        fitWindow.setChecked(Qt.Checked)
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action(
            # self.tr("&Edit Label"),
            self.tr("&编辑标签"),
            self.editLabel,
            shortcuts["edit_label"],
            "edit",
            self.tr("Modify the label of the selected polygon"),
            enabled=False,
        )

        fill_drawing = action(
            # self.tr("Fill Drawing Polygon"),
            self.tr("填充所绘多边形"),
            self.canvas.setFillDrawing,
            None,
            "color",
            self.tr("Fill polygon while drawing"),
            checkable=True,
            enabled=True,
        )
        fill_drawing.trigger()

        # Lavel list context menu.
        labelMenu = QtWidgets.QMenu()
        utils.addActions(labelMenu, (edit, delete))
        # print('进入10')
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu
        )

        # Store actions for further handling.
        self.actions = utils.struct(
            saveAuto=saveAuto,
            saveWithImageData=saveWithImageData,
            changeOutputDir=changeOutputDir,
            save=save,
            saveAs=saveAs,
            open=open_,
            close=close,
            deleteFile=deleteFile,
            toggleKeepPrevMode=toggle_keep_prev_mode,
            delete=delete,
            edit=edit,
            copy=copy,
            undoLastPoint=undoLastPoint,
            undo=undo,
            addPointToEdge=addPointToEdge,
            removePoint=removePoint,
            createMode=createMode,
            editMode=editMode,
            createRectangleMode=createRectangleMode,
            createCircleMode=createCircleMode,
            createLineMode=createLineMode,
            createPointMode=createPointMode,
            createLineStripMode=createLineStripMode,
            zoom=zoom,
            zoomIn=zoomIn,
            zoomOut=zoomOut,
            zoomOrg=zoomOrg,
            fitWindow=fitWindow,
            fitWidth=fitWidth,
            brightnessContrast=brightnessContrast,
            zoomActions=zoomActions,
            openNextImg=openNextImg,
            openPrevImg=openPrevImg,
            fileMenuActions=(open_, opendir, save, saveAs, close, quit),
            tool=(),
            # XXX: need to add some actions here to activate the shortcut
            editMenu=(
                edit,
                copy,
                delete,
                None,
                undo,
                undoLastPoint,
                None,
                addPointToEdge,
                None,
                toggle_keep_prev_mode,
            ),
            # menu shown at right click
            menu=(
                createMode,
                createRectangleMode,
                createCircleMode,
                createLineMode,
                createPointMode,
                createLineStripMode,
                editMode,
                edit,
                copy,
                delete,
                undo,
                undoLastPoint,
                addPointToEdge,
                removePoint,
            ),
            onLoadActive=(
                close,
                createMode,
                createRectangleMode,
                createCircleMode,
                createLineMode,
                createPointMode,
                createLineStripMode,
                editMode,
                brightnessContrast,
            ),
            onShapesPresent=(saveAs, hideAll, showAll),
        )

        self.canvas.edgeSelected.connect(self.canvasShapeEdgeSelected)
        self.canvas.vertexSelected.connect(self.actions.removePoint.setEnabled)

        self.menus = utils.struct(
            # file=self.menu(self.tr("&File")),
            # edit=self.menu(self.tr("&Edit")),
            # view=self.menu(self.tr("&View")),
            # help=self.menu(self.tr("&Help")),
            # recentFiles=QtWidgets.QMenu(self.tr("Open &Recent")),
            activate=self.menu(self.tr("&激活")),
            file=self.menu(self.tr("&文件")),
            edit=self.menu(self.tr("&编辑")),
            view=self.menu(self.tr("&视图")),
            # help=self.menu(self.tr("&帮助")),
            select=self.menu(self.tr("&产品类型")),
            select_name=self.menu(self.tr("&👆字符👆")),
            # recentFiles=QtWidgets.QMenu(self.tr("Open &Recent")),
            recentFiles=QtWidgets.QMenu(self.tr("&最近打开")),
            labelList=labelMenu,
        )


        #按钮
        sel1 = action(
            "&冷轧",
            self.getClsNameLZ,
            "更新冷轧类别列表",
            # checkable=True,
            # icon="done",
            # checkable=True,

        )
        sel2 = action(
            "&热轧",
            self.getClsNameRZ,
            "更新热轧类别列表",
            # checkable=True,
        )
        sel3 = action(
            "&板材",
            self.getClsNameBC,
            "更新板材类别列表",
            # checkable=True,
        )
        sel4 = action(
            "&棒材",
            self.getClsNameCB,
            "更新棒材类别列表",
            # checkable=True,
        )
        sel5 = action(
            "&铸坯",
            self.getClsNameZP,
            "更新连铸坯类别列表",
            # checkable=True,
        )
        sel6=action(
            "&字符",
            self.getClsNameZF,
            "更新字符类别列表",
            # checkable=True,
        )

        Activate = action(
            "&激活产品切换功能",
            self.toYes,
        )
        Deactivate = action(
            "&停止产品切换功能",
            self.toNo,
        )
        utils.addActions(
            self.menus.activate,
            (
                Activate,
                Deactivate,
            ),
        )
        #产品类型
        utils.addActions(
            self.menus.select,
            (
                sel1,
                sel2,
                sel3,
                sel4,
                sel5,
                sel6,
            ),
        )

        utils.addActions(
            self.menus.file,
            (
                open_,
                openNextImg,
                openPrevImg,
                opendir,
                self.menus.recentFiles,
                save,
                saveAs,
                saveAuto,
                changeOutputDir,
                saveWithImageData,
                close,
                deleteFile,
                None,
                quit,
            ),
        )
        # utils.addActions(self.menus.help, (help,))
        utils.addActions(
            self.menus.view,
            (
                self.flag_dock.toggleViewAction(),
                self.label_dock.toggleViewAction(),
                self.shape_dock.toggleViewAction(),
                self.file_dock.toggleViewAction(),
                None,
                fill_drawing,
                None,
                hideAll,
                showAll,
                None,
                zoomIn,
                zoomOut,
                zoomOrg,
                None,
                fitWindow,
                fitWidth,
                None,
                brightnessContrast,
            ),
        )

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

        # Custom context menu for the canvas widget:
        utils.addActions(self.canvas.menus[0], self.actions.menu)
        utils.addActions(
            self.canvas.menus[1],
            (
                # action("&Copy here", self.copyShape),
                # action("&Move here", self.moveShape),
                action("&复制到这里", self.copyShape),
                action("&移动到这里", self.moveShape),
            ),
        )

        self.tools = self.toolbar("Tools")
        # Menu buttons on Left
        self.actions.tool = (
            open_,
            opendir,
            openNextImg,
            openPrevImg,
            save,
            deleteFile,
            None,
            createMode,
            editMode,
            copy,
            delete,
            undo,
            brightnessContrast,
            None,
            zoom,
            fitWidth,
        )

        self.statusBar().showMessage(self.tr("%s started.") % __appname__)
        self.statusBar().show()

        if output_file is not None and self._config["auto_save"]:
            logger.warn(
                "If `auto_save` argument is True, `output_file` argument "
                "is ignored and output filename is automatically "
                "set as IMAGE_BASENAME.json."
            )
        self.output_file = output_file
        self.output_dir = output_dir

        # Application state.
        self.image = QtGui.QImage()
        self.imagePath = None
        self.recentFiles = []
        self.maxRecent = 7
        self.otherData = None
        self.zoom_level = 100
        self.fit_window = False
        self.zoom_values = {}  # key=filename, value=(zoom_mode, zoom_value)
        self.brightnessContrast_values = {}
        self.scroll_values = {
            Qt.Horizontal: {},
            Qt.Vertical: {},
        }  # key=filename, value=scroll_value

        if filename is not None and osp.isdir(filename):
            self.importDirImages(filename, load=False)
        else:
            self.filename = filename

        if config["file_search"]:
            self.fileSearch.setText(config["file_search"])
            self.fileSearchChanged()

        # XXX: Could be completely declarative.
        # Restore application settings.
        self.settings = QtCore.QSettings("labelme", "labelme")
        # FIXME: QSettings.value can return None on PyQt4
        self.recentFiles = self.settings.value("recentFiles", []) or []
        size = self.settings.value("window/size", QtCore.QSize(600, 500))
        position = self.settings.value("window/position", QtCore.QPoint(0, 0))
        self.resize(size)
        self.move(position)
        # or simply:
        # self.restoreGeometry(settings['window/geometry']
        self.restoreState(
            self.settings.value("window/state", QtCore.QByteArray())
        )

        # Populate the File menu dynamically.
        self.updateFileMenu()
        # Since loading the file may take some time,
        # make sure it runs in the background.
        if self.filename is not None:
            self.queueEvent(functools.partial(self.loadFile, self.filename))

        # Callbacks:
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        self.populateModeActions()

        # self.firstStart = True
        # if self.firstStart:
        #    QWhatsThis.enterWhatsThisMode()

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            utils.addActions(menu, actions)
        return menu

    def menu_show(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            utils.addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName("%sToolBar" % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            utils.addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar

    # Support Functions

    def noShapes(self):
        # print('进入noShapes')
        return not len(self.labelList)

    def populateModeActions(self):
        tool, menu = self.actions.tool, self.actions.menu
        self.tools.clear()
        utils.addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        utils.addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (
            self.actions.createMode,
            self.actions.createRectangleMode,
            self.actions.createCircleMode,
            self.actions.createLineMode,
            self.actions.createPointMode,
            self.actions.createLineStripMode,
            self.actions.editMode,
        )
        utils.addActions(self.menus.edit, actions + self.actions.editMenu)

    def setDirty(self):
        #print('进入setDirty函数')
        # Even if we autosave the file, we keep the ability to undo
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

        if self._config["auto_save"] or self.actions.saveAuto.isChecked():
            label_file = osp.splitext(self.imagePath)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            self.saveLabels(label_file)
            return
        self.dirty = True
        self.actions.save.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = "{} - {}*".format(title, self.filename)
        self.setWindowTitle(title)
        #print('跳出setDirty函数')

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.createMode.setEnabled(True)
        self.actions.createRectangleMode.setEnabled(True)
        self.actions.createCircleMode.setEnabled(True)
        self.actions.createLineMode.setEnabled(True)
        self.actions.createPointMode.setEnabled(True)
        self.actions.createLineStripMode.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = "{} - {}".format(title, self.filename)
        self.setWindowTitle(title)

        if self.hasLabelFile():
            self.actions.deleteFile.setEnabled(True)
        else:
            self.actions.deleteFile.setEnabled(False)

    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)

    def canvasShapeEdgeSelected(self, selected, shape):
        self.actions.addPointToEdge.setEnabled(
            selected and shape and shape.canAddPoint()
        )

    def queueEvent(self, function):
        QtCore.QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        # print('进入resetState')
        self.labelList.clear()
        self.filename = None
        self.imagePath = None
        self.imageData = None
        self.labelFile = None
        self.otherData = None
        self.canvas.resetState()

    def currentItem(self):
        # print('进入currentItem')
        items = self.labelList.selectedItems()
        # print(f'item长度:{len(items)}')
        if items:
            return items[0]
        return None

    def addRecentFile(self, filename):
        if filename in self.recentFiles:
            self.recentFiles.remove(filename)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filename)

    # Callbacks

    def undoShapeEdit(self):
        # print('进入undoShapeEdit')
        self.canvas.restoreShape()
        self.labelList.clear()
        self.loadShapes(self.canvas.shapes)
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)
        print('撤销按钮是否变黑：',self.canvas.isShapeRestorable)
        self.actions.save.setEnabled(True)

    def tutorial(self):
        url = "https://github.com/wkentaro/labelme/tree/master/examples/tutorial"  # NOQA
        webbrowser.open(url)

    def toggleDrawingSensitive(self, drawing=True):
        """Toggle drawing sensitive.

        In the middle of drawing, toggling between modes should be disabled.
        """
        self.actions.editMode.setEnabled(not drawing)
        self.actions.undoLastPoint.setEnabled(drawing)
        self.actions.undo.setEnabled(not drawing)
        self.actions.delete.setEnabled(not drawing)

    def toggleDrawMode(self, edit=True, createMode="polygon"):
        self.canvas.setEditing(edit)
        self.canvas.createMode = createMode
        if edit:
            self.actions.createMode.setEnabled(True)
            self.actions.createRectangleMode.setEnabled(True)
            self.actions.createCircleMode.setEnabled(True)
            self.actions.createLineMode.setEnabled(True)
            self.actions.createPointMode.setEnabled(True)
            self.actions.createLineStripMode.setEnabled(True)
        else:
            if createMode == "polygon":
                self.actions.createMode.setEnabled(False)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == "rectangle":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(False)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == "line":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(False)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == "point":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(False)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == "circle":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(False)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == "linestrip":
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(False)
            else:
                raise ValueError("Unsupported createMode: %s" % createMode)
        self.actions.editMode.setEnabled(not edit)

    def setEditMode(self):
        self.toggleDrawMode(True)

    def updateFileMenu(self):
        current = self.filename

        def exists(filename):
            return osp.exists(str(filename))

        menu = self.menus.recentFiles
        menu.clear()
        #files 文件列表
        files = [f for f in self.recentFiles if f != current and exists(f)]
        for i, f in enumerate(files):
            icon = utils.newIcon("labels")
            action = QtWidgets.QAction(
                icon, "&%d %s" % (i + 1, QtCore.QFileInfo(f).fileName()), self
            )
            action.triggered.connect(functools.partial(self.loadRecent, f))
            menu.addAction(action)

    def popLabelListMenu(self, point):
        # print('进入popLabelListMenu')
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point))

    def validateLabel(self, label):
        # no validation
        if self._config["validate_label"] is None:
            return True

        for i in range(self.uniqLabelList.count()):
            label_i = self.uniqLabelList.item(i).data(Qt.UserRole)
            if self._config["validate_label"] in ["exact"]:
                if label_i == label:
                    return True
        return False

    def editLabel(self, item=None):
        if item and not isinstance(item, LabelListWidgetItem):
            raise TypeError("item must be LabelListWidgetItem type")
        if not self.canvas.editing():
            return
        if not item:
            item = self.currentItem()
        if item is None:
            return
        shape = item.shape()
        if shape is None:
            return
        #测试代码
        # print(f"shape.label:{shape.label}")
        # print(f"shape.flags:{shape.flags}")
        # print(f"shape.group_id:{shape.group_id}")
        # # print(f"shape.Chineselabel:{shape.Chineselabel}")
        # # print(f"shape.difficult:{shape.difficult}")
        # # print(f"shape.definition:{shape.definition}")
        # print(f"shape.label_ch:{shape.label_ch}")
        # print(f"shape.label_dif:{shape.label_dif}")
        # print(f"shape.label_imgdif:{shape.label_imgdif}")
        # if shape.Chineselabel is None:
        #     shape.Chineselabel = self.ch_name
        # if shape.difficult is None:
        #     shape.difficult = '9'
        # if shape.definition is None:
        #     shape.definition= '9'
        # self.errorMessage(
        #     self.tr("提示:"),
        #     self.tr("None信息使用默认值替换！！")
        # )


        try:
            text_ch = shape.label_ch
        except:
            text_ch = shape.chineselabel

        try:
            t_dif = shape.label_dif
        except:
            t_dif = shape.confidence

        try:
            t_imgdef = shape.label_imgdif
        except:
            t_imgdef = shape.definition

        try:
            t_objdef = shape.label_objdif
        except:
            t_objdef = shape.obj_definition
        print('>>>>>11111111111')
        text, flags, group_id,text_ch,text_dif,text_objdif,text_imgdif = self.labelDialog.popUp(
            text=shape.label,
            flags=shape.flags,
            group_id=shape.group_id,
            text_ch= text_ch,
            text_dif=t_dif,
            text_imgdif=t_imgdef,
            text_objdif=t_objdef,
        )
        print('11111111111<<<<<<<<<<<<<<<')
        if text is None:
            return
        if not self.validateLabel(text):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    text, self._config["validate_label"]
                ),
            )
            return
        shape.label = text
        shape.flags = flags
        shape.group_id = group_id
        shape.chineselabel = text_ch
        shape.confidence = text_dif
        shape.definition = text_imgdif
        shape.obj_definition = text_objdif

        shape.label_ch = text_ch
        shape.label_dif = text_dif
        shape.label_imgdif = text_imgdif
        shape.label_objdif = text_objdif

        if shape.group_id is None:
            #item.setText(shape.label)
            item.setText("{} ({}) ({}) ({}) ({}) ({})".format(shape.label, shape.group_id,shape.chineselabel,shape.confidence,shape.definition,shape.obj_definition))
        else:
            item.setText("{} ({})".format(shape.label, shape.group_id))
        self.setDirty()
        #print('已进入setDirty函数1')
        if not self.uniqLabelList.findItemsByLabel(shape.label):
            item = QtWidgets.QListWidgetItem()
            item.setData(Qt.UserRole, shape.label)
            self.uniqLabelList.addItem(item)

    def fileSearchChanged(self):
        self.importDirImages(
            self.lastOpenDir,
            pattern=self.fileSearch.text(),
            load=False,
        )

    def fileSelectionChanged(self):
        items = self.fileListWidget.selectedItems()
        if not items:
            return
        item = items[0]

        if not self.mayContinue():
            return

        currIndex = self.imageList.index(str(item.text()))
        if currIndex < len(self.imageList):
            filename = self.imageList[currIndex]
            if filename:
                self.loadFile(filename)

    # React to canvas signals.
    def shapeSelectionChanged(self, selected_shapes):
        self._noSelectionSlot = True
        for shape in self.canvas.selectedShapes:
            shape.selected = False
        self.labelList.clearSelection()
        self.canvas.selectedShapes = selected_shapes
        for shape in self.canvas.selectedShapes:
            shape.selected = True
            item = self.labelList.findItemByShape(shape)
            self.labelList.selectItem(item)
            self.labelList.scrollToItem(item)
        self._noSelectionSlot = False
        n_selected = len(selected_shapes)
        self.actions.delete.setEnabled(n_selected)
        self.actions.copy.setEnabled(n_selected)
        self.actions.edit.setEnabled(n_selected == 1)


    def addLabel(self, shape):
        if shape.group_id is None:
            try:
                text = shape.label
            except:
                text = ''
            ##
            try:
                text_ch = shape.label_ch
            except:
                text_ch = shape.chineselabel
            ##
            try:
                text_dif = shape.label_dif
            except:
                text_dif = shape.confidence
            try:
                text_imgdif = shape.label_imgdif
            except:
                text_imgdif = shape.definition
            try:
                text_objdif = shape.label_objdif
            except:
                text_objdif = shape.obj_definition

            #text = text0 +" "+ text_ch +" "+ text_dif+" " + text_imgdif
            print('addLabel',text,text_ch,text_dif,text_objdif,text_imgdif)
        else:
            text = "{} ({})".format(shape.label, shape.group_id)
            # text = "{}{}{} ({})".format(shape.label,shape.label_ch, shape.label_dif,shape.group_id)
        # text = shape.label +" "+ shape.chineselabel +" "+ shape.confidence+" " + shape.obj_definition+" " + shape.group_id +" " +shape.definition
        shape.label = text
        shape.chineselabel = text_ch
        shape.confidence = text_dif
        shape.obj_definition = text_objdif
        shape.definition = text_imgdif
        print('addLabel_shape_one:',shape.label,shape.chineselabel,shape.confidence,shape.obj_definition,shape.definition)

        label_list_item = LabelListWidgetItem(text, shape)
        # print(label_list_item)
        self.labelList.addItem(label_list_item)
        #print(list(self.labelList))

        if not self.uniqLabelList.findItemsByLabel(shape.label):
            item = self.uniqLabelList.createItemFromLabel(shape.label)
            self.uniqLabelList.addItem(item)
            rgb = self._get_rgb_by_label(shape.label)
            self.uniqLabelList.setItemLabel(item, shape.label, rgb)
        self.labelDialog.addLabelHistory(shape.label)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)
        rgb = self._get_rgb_by_label(shape.label)
        r, g, b = rgb
        label_list_item.setText(
            '{} <font color="#{:02x}{:02x}{:02x}">●</font>'.format(
                text, r, g, b
            )
        )
        shape.line_color = QtGui.QColor(r, g, b)
        shape.vertex_fill_color = QtGui.QColor(r, g, b)
        shape.hvertex_fill_color = QtGui.QColor(255, 255, 255)
        shape.fill_color = QtGui.QColor(r, g, b, 128)
        shape.select_line_color = QtGui.QColor(255, 255, 255)
        shape.select_fill_color = QtGui.QColor(r, g, b, 155)
    def _get_rgb_by_label(self, label):
        if self._config["shape_color"] == "auto":
            item = self.uniqLabelList.findItemsByLabel(label)[0]
            label_id = self.uniqLabelList.indexFromItem(item).row() + 1
            label_id += self._config["shift_auto_shape_color"]
            return LABEL_COLORMAP[label_id % len(LABEL_COLORMAP)]
        elif (
            self._config["shape_color"] == "manual"
            and self._config["label_colors"]
            and label in self._config["label_colors"]
        ):
            return self._config["label_colors"][label]
        elif self._config["default_shape_color"]:
            return self._config["default_shape_color"]

    def remLabels(self, shapes):
        # print('进入remLabels')
        for shape in shapes:
            item = self.labelList.findItemByShape(shape)
            self.labelList.removeItem(item)

    def loadShapes(self, shapes, replace=True):
        self._noSelectionSlot = True
        for shape in shapes:
            self.addLabel(shape)
        self.labelList.clearSelection()
        self._noSelectionSlot = False
        self.canvas.loadShapes(shapes, replace=replace)

    def loadLabels(self, shapes,definition=None):

        s = []
        for shape in shapes:
            label = shape["label"]
            label_ch = shape["label_ch"]
            confidence = shape["label_dif"]
            obj_definition = shape['label_objdif']
            points = shape["points"]
            shape_type = shape["shape_type"]
            flags = shape["flags"]
            group_id = shape["group_id"]
            other_data = shape["other_data"]
            if not points:
                # skip point-empty shape
                continue
            shape = Shape(
                label=label,
                shape_type=shape_type,
                group_id=group_id,
            )
            for x, y in points:
                shape.addPoint(QtCore.QPointF(x, y))
            shape.close()

            default_flags = {}
            if self._config["label_flags"]:
                for pattern, keys in self._config["label_flags"].items():
                    if re.match(pattern, label):
                        for key in keys:
                            default_flags[key] = False
            shape.flags = default_flags
            shape.flags.update(flags)
            shape.other_data = other_data
            shape.chineselabel = label_ch
            shape.confidence = confidence
            shape.definition =definition
            shape.obj_definition = obj_definition
            s.append(shape)
        self.loadShapes(s)

    def loadFlags(self, flags):
        self.flag_widget.clear()
        for key, flag in flags.items():
            item = QtWidgets.QListWidgetItem(key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
            self.flag_widget.addItem(item)

    def saveLabels(self, filename):
        #print('进入saveLabels')
        lf = LabelFile()
        def format_shape(s):
            data = s.other_data.copy()
            try:
                data.update(
                    dict(
                        label=s.label.encode("utf-8") if PY2 else s.label,
                        chineselabel=s.label.encode("utf-8") if PY2 else s.label_ch,
                        confidence=s.label.encode("utf-8") if PY2 else s.label_dif,
                        definition=s.label.encode("utf-8") if PY2 else s.label_objdif,
                        points=[(p.x(), p.y()) for p in s.points],
                        group_id=s.group_id,
                        shape_type=s.shape_type,
                        flags=s.flags,
                    )
                )
            except:
                data.update(
                    dict(
                        label=s.label.encode("utf-8") if PY2 else s.label,
                        chineselabel=s.label.encode("utf-8") if PY2 else s.chineselabel,
                        confidence=s.label.encode("utf-8") if PY2 else s.confidence,
                        definition=s.label.encode("utf-8") if PY2 else s.obj_definition,
                        points=[(p.x(), p.y()) for p in s.points],
                        group_id=s.group_id,
                        shape_type=s.shape_type,
                        flags=s.flags,
                    )
                )

            return data
        shapes = [format_shape(item.shape()) for item in self.labelList]
        print('shapes：',shapes)
        print('item.shape()：')
        print([item.shape() for item in self.labelList])
        img_defi = ''
        try:
            img_defi = [item.shape().label_imgdif for item in self.labelList][-1]
            print('try_img_defi：',img_defi)
        except:
            info_decide = [item.shape().definition for item in self.labelList]
            print('except_info_decide：', info_decide)
            if len(info_decide) != 0:
                img_defi = [item.shape().definition for item in self.labelList][-1]
            elif len(info_decide) == 0:
                img_defi = '9'
            print('except_img_defi：',img_defi)
        flags = {}
        for i in range(self.flag_widget.count()):
            item = self.flag_widget.item(i)
            key = item.text()
            flag = item.checkState() == Qt.Checked
            flags[key] = flag
        try:
            imagePath = osp.relpath(self.imagePath, osp.dirname(filename))
            imageData = self.imageData if self._config["store_data"] else None
            if osp.dirname(filename) and not osp.exists(osp.dirname(filename)):
                os.makedirs(osp.dirname(filename))
            lf.save(
                filename=filename,
                shapes=shapes,
                imagePath=imagePath,
                imageData=imageData,
                imageHeight=self.image.height(),
                imageWidth=self.image.width(),
                otherData=self.otherData,
                flags=flags,
                definition=img_defi,
            )
            self.labelFile = lf
            items = self.fileListWidget.findItems(
                self.imagePath, Qt.MatchExactly
            )
            if len(items) > 0:
                if len(items) != 1:
                    raise RuntimeError("There are duplicate files.")
                items[0].setCheckState(Qt.Checked)
            # disable allows next and previous image to proceed
            # self.filename = filename
            return True
        except LabelFileError as e:
            self.errorMessage(
                self.tr("Error saving label data"), self.tr("<b>%s</b>") % e
            )
            return False

    def copySelectedShape(self):
        # print('进入copySelectedShape')
        added_shapes = self.canvas.copySelectedShapes()
        self.labelList.clearSelection()
        for shape in added_shapes:
            self.addLabel(shape)
        self.setDirty()

    def labelSelectionChanged(self):
        # print('进入labelSelectionChanged')
        if self._noSelectionSlot:
            return
        if self.canvas.editing():
            selected_shapes = []
            for item in self.labelList.selectedItems():
                selected_shapes.append(item.shape())
            if selected_shapes:
                self.canvas.selectShapes(selected_shapes)
            else:
                self.canvas.deSelectShape()

    def labelItemChanged(self, item):
        shape = item.shape()
        self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)

    def labelOrderChanged(self):
        # print('进入labelOrderChanged')
        self.setDirty()
        self.canvas.loadShapes([item.shape() for item in self.labelList])

    # Callback functions:

    def newShape(self):
        # print('进入newShape')
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """
        items = self.uniqLabelList.selectedItems()
        text = None
        if items:
            text = items[0].data(Qt.UserRole)
        flags = {}
        group_id = None
        if self._config["display_label_popup"] or not text:
            previous_text = self.labelDialog.edit.text()
            # previous_text1 = self.labelDialog.edit1.text()
            #标注框停留位置and输入标签停留地
            print('>>>>>>>>>2222222222222222222')
            text, flags, group_id,text_ch,text_dif,text_objdif,text_imgdif = self.labelDialog.popUp(text)
            print(text, flags, group_id,text_ch,text_dif,text_objdif,text_imgdif)
            self.ch_name = text_ch
            print('2222222222222222<<<<<<<<<<<<<<')
            if not text:
                # pass
                self.labelDialog.edit.setText(previous_text)
                # self.labelDialog.edit1.setText(previous_text1)

        if text and not self.validateLabel(text):
            self.errorMessage(
                self.tr("Invalid label"),
                self.tr("Invalid label '{}' with validation type '{}'").format(
                    text, self._config["validate_label"]
                ),
            )
            text = ""
        if text:
            # print(f'text_flags:{text,flags}')
            self.labelList.clearSelection()
            shape = self.canvas.setLastLabel(text, flags)
            shape.group_id = group_id
            shape.label_ch = text_ch
            shape.label_dif = text_dif
            shape.label_imgdif = text_imgdif
            shape.label_objdif = text_objdif
            self.addLabel(shape)
            self.actions.editMode.setEnabled(True)
            self.actions.undoLastPoint.setEnabled(False)
            self.actions.undo.setEnabled(True)
            self.setDirty()
            #print('已进入setDirty函数4')
        else:
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()

    def scrollRequest(self, delta, orientation):
        units = -delta * 0.1  # natural scroll
        bar = self.scrollBars[orientation]
        value = bar.value() + bar.singleStep() * units
        self.setScroll(orientation, value)

    def setScroll(self, orientation, value):
        self.scrollBars[orientation].setValue(value)
        self.scroll_values[orientation][self.filename] = value

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def addZoom(self, increment=1.1):
        zoom_value = self.zoomWidget.value() * increment
        if increment > 1:
            zoom_value = math.ceil(zoom_value)
        else:
            zoom_value = math.floor(zoom_value)
        self.setZoom(zoom_value)

    def zoomRequest(self, delta, pos):
        canvas_width_old = self.canvas.width()
        units = 1.1
        if delta < 0:
            units = 0.9
        self.addZoom(units)

        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old

            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()

            self.setScroll(
                Qt.Horizontal,
                self.scrollBars[Qt.Horizontal].value() + x_shift,
            )
            self.setScroll(
                Qt.Vertical,
                self.scrollBars[Qt.Vertical].value() + y_shift,
            )

    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()

    def onNewBrightnessContrast(self, qimage):
        self.canvas.loadPixmap(
            QtGui.QPixmap.fromImage(qimage), clear_shapes=False
        )

    def brightnessContrast(self, value):
        dialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        dialog.exec_()

        brightness = dialog.slider_brightness.value()
        contrast = dialog.slider_contrast.value()
        self.brightnessContrast_values[self.filename] = (brightness, contrast)

    def togglePolygons(self, value):
        # print('进入togglePolygons')
        for item in self.labelList:
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def loadFile(self, filename=None):
        """Load the specified file, or the last opened file if None."""
        # changing fileListWidget loads file
        if filename in self.imageList and (
            self.fileListWidget.currentRow() != self.imageList.index(filename)
        ):
            self.fileListWidget.setCurrentRow(self.imageList.index(filename))
            self.fileListWidget.repaint()
            return

        self.resetState()
        self.canvas.setEnabled(False)
        if filename is None:
            filename = self.settings.value("filename", "")
        filename = str(filename)
        if not QtCore.QFile.exists(filename):
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr("No such file: <b>%s</b>") % filename,
            )
            return False
        # assumes same name, but json extension
        self.status(self.tr("Loading %s...") % osp.basename(str(filename)))
        label_file = osp.splitext(filename)[0] + ".json"
        if self.output_dir:
            label_file_without_path = osp.basename(label_file)
            label_file = osp.join(self.output_dir, label_file_without_path)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
            label_file
        ):
            try:
                self.labelFile = LabelFile(label_file)
            except LabelFileError as e:
                self.errorMessage(
                    self.tr("Error opening file"),
                    self.tr(
                        "<p><b>%s</b></p>"
                        "<p>Make sure <i>%s</i> is a valid label file."
                    )
                    % (e, label_file),
                )
                self.status(self.tr("Error reading %s") % label_file)
                return False
            self.imageData = self.labelFile.imageData
            self.imagePath = osp.join(
                osp.dirname(label_file),
                self.labelFile.imagePath,
            )
            self.otherData = self.labelFile.otherData
        else:
            self.imageData = LabelFile.load_image_file(filename)
            if self.imageData:
                self.imagePath = filename
            self.labelFile = None
        image = QtGui.QImage.fromData(self.imageData)

        if image.isNull():
            formats = [
                "*.{}".format(fmt.data().decode())
                for fmt in QtGui.QImageReader.supportedImageFormats()
            ]
            self.errorMessage(
                self.tr("Error opening file"),
                self.tr(
                    "<p>Make sure <i>{0}</i> is a valid image file.<br/>"
                    "Supported image formats: {1}</p>"
                ).format(filename, ",".join(formats)),
            )
            self.status(self.tr("Error reading %s") % filename)
            return False
        self.image = image
        self.filename = filename
        if self._config["keep_prev"]:
            prev_shapes = self.canvas.shapes
            # print(f"prev_shapes:{prev_shapes}")
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
        flags = {k: False for k in self._config["flags"] or []}
        if self.labelFile:
            #加载shapes(和json文件对应)和definition
            definition = self.labelFile.definition
            self.loadLabels(self.labelFile.shapes,definition=definition)
            if self.labelFile.flags is not None:
                flags.update(self.labelFile.flags)
        self.loadFlags(flags)
        if self._config["keep_prev"] and self.noShapes():
            self.loadShapes(prev_shapes, replace=False)
            self.setDirty()
            #print('已进入setDirty函数5')
        else:
            self.setClean()
        self.canvas.setEnabled(True)
        # set zoom values
        is_initial_load = not self.zoom_values
        if self.filename in self.zoom_values:
            self.zoomMode = self.zoom_values[self.filename][0]
            self.setZoom(self.zoom_values[self.filename][1])
        elif is_initial_load or not self._config["keep_prev_scale"]:
            self.adjustScale(initial=True)
        # set scroll values
        for orientation in self.scroll_values:
            if self.filename in self.scroll_values[orientation]:
                self.setScroll(
                    orientation, self.scroll_values[orientation][self.filename]
                )
        # set brightness constrast values
        dialog = BrightnessContrastDialog(
            utils.img_data_to_pil(self.imageData),
            self.onNewBrightnessContrast,
            parent=self,
        )
        brightness, contrast = self.brightnessContrast_values.get(
            self.filename, (None, None)
        )
        if self._config["keep_prev_brightness"] and self.recentFiles:
            brightness, _ = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if self._config["keep_prev_contrast"] and self.recentFiles:
            _, contrast = self.brightnessContrast_values.get(
                self.recentFiles[0], (None, None)
            )
        if brightness is not None:
            dialog.slider_brightness.setValue(brightness)
        if contrast is not None:
            dialog.slider_contrast.setValue(contrast)
        self.brightnessContrast_values[self.filename] = (brightness, contrast)
        if brightness is not None or contrast is not None:
            dialog.onNewValue(None)
        self.paintCanvas()
        self.addRecentFile(self.filename)
        self.toggleActions(True)
        self.canvas.setFocus()
        self.status(self.tr("Loaded %s") % osp.basename(str(filename)))
        return True

    def resizeEvent(self, event):
        if (
            self.canvas
            and not self.image.isNull()
            and self.zoomMode != self.MANUAL_ZOOM
        ):
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        value = int(100 * value)
        self.zoomWidget.setValue(value)
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def enableSaveImageWithData(self, enabled):
        self._config["store_data"] = enabled
        self.actions.saveWithImageData.setChecked(enabled)

    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        self.settings.setValue(
            "filename", self.filename if self.filename else ""
        )
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue("recentFiles", self.recentFiles)
        # ask the use for where to save the labels
        # self.settings.setValue('window/geometry', self.saveGeometry())

    def dragEnterEvent(self, event):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        if event.mimeData().hasUrls():
            items = [i.toLocalFile() for i in event.mimeData().urls()]
            if any([i.lower().endswith(tuple(extensions)) for i in items]):
                event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not self.mayContinue():
            event.ignore()
            return
        items = [i.toLocalFile() for i in event.mimeData().urls()]
        self.importDroppedImageFiles(items)

    # User Dialogs #

    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    def openPrevImg(self, _value=False):
        keep_prev = self._config["keep_prev"]
        if Qt.KeyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._config["keep_prev"] = True

        if not self.mayContinue():
            return

        if len(self.imageList) <= 0:
            return

        if self.filename is None:
            return

        currIndex = self.imageList.index(self.filename)
        if currIndex - 1 >= 0:
            filename = self.imageList[currIndex - 1]
            if filename:
                self.loadFile(filename)

        self._config["keep_prev"] = keep_prev

    def openNextImg(self, _value=False, load=True):
        keep_prev = self._config["keep_prev"]
        if Qt.KeyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._config["keep_prev"] = True

        if not self.mayContinue():
            return

        if len(self.imageList) <= 0:
            return

        filename = None
        if self.filename is None:
            filename = self.imageList[0]
        else:
            try:
                currIndex = self.imageList.index(self.filename)
            except:
                #print(self.filename)
                currIndex = -1
            if currIndex + 1 < len(self.imageList):
                filename = self.imageList[currIndex + 1]
            else:
                filename = self.imageList[-1]
        self.filename = filename

        if self.filename and load:
            self.loadFile(self.filename)

        self._config["keep_prev"] = keep_prev

    def openFile(self, _value=False):
        if not self.mayContinue():
            return
        path = osp.dirname(str(self.filename)) if self.filename else "."
        formats = [
            "*.{}".format(fmt.data().decode())
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        filters = self.tr("Image & Label files (%s)") % " ".join(
            formats + ["*%s" % LabelFile.suffix]
        )
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("%s - Choose Image or Label file") % __appname__,
            path,
            filters,
        )
        if QT5:
            filename, _ = filename
        filename = str(filename)
        if filename:
            self.loadFile(filename)

    def changeOutputDirDialog(self, _value=False):
        default_output_dir = self.output_dir
        if default_output_dir is None and self.filename:
            default_output_dir = osp.dirname(self.filename)
        if default_output_dir is None:
            default_output_dir = self.currentPath()

        output_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("%s - Save/Load Annotations in Directory") % __appname__,
            default_output_dir,
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        output_dir = str(output_dir)

        if not output_dir:
            return

        self.output_dir = output_dir

        self.statusBar().showMessage(
            self.tr("%s . Annotations will be saved/loaded in %s")
            % ("Change Annotations Dir", self.output_dir)
        )
        self.statusBar().show()

        current_filename = self.filename
        self.importDirImages(self.lastOpenDir, load=False)

        if current_filename in self.imageList:
            # retain currently selected file
            self.fileListWidget.setCurrentRow(
                self.imageList.index(current_filename)
            )
            self.fileListWidget.repaint()

    def saveFile(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        # try:
        if self.labelFile:
            print('!!!!!!!!!')
            # DL20180323 - overwrite when in directory
            print('self.labelFile.filename：',self.labelFile.filename)
            self._saveFile(self.labelFile.filename)
        elif self.output_file:
            print('@@@@@@@@@@@')
            self._saveFile(self.output_file)
            self.close()
        else:
            print('#########')
            self._saveFile(self.saveFileDialog())
        # except:
        #     self.errorMessage(
        #         self.tr("操作错误|操作取消"),
        #         self.tr(
        #             "如果是操作取消:请重新选择！"
        #             "其它情况:请删除框重新操作！"
        #         ),
        #     )

    def saveFileAs(self, _value=False):
        #print('进入调用_saveFile函数的saveFileAs函数')
        assert not self.image.isNull(), "cannot save empty image"
        self._saveFile(self.saveFileDialog())

    def saveFileDialog(self):
        caption = self.tr("%s - Choose File") % __appname__
        filters = self.tr("Label files (*%s)") % LabelFile.suffix
        if self.output_dir:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.output_dir, filters
            )
        else:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.currentPath(), filters
            )
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
        basename = osp.basename(osp.splitext(self.filename)[0])
        if self.output_dir:
            default_labelfile_name = osp.join(
                self.output_dir, basename + LabelFile.suffix
            )
        else:
            default_labelfile_name = osp.join(
                self.currentPath(), basename + LabelFile.suffix
            )
        filename = dlg.getSaveFileName(
            self,
            self.tr("Choose File"),
            default_labelfile_name,
            self.tr("Label files (*%s)") % LabelFile.suffix,
        )
        if isinstance(filename, tuple):
            filename, _ = filename
        return filename

    def _saveFile(self, filename):
        print('进去_saveFile函数')
        #print('self.saveLabels(filename:',self.saveLabels(filename))
        if filename and self.saveLabels(filename):
            self.addRecentFile(filename)
            self.setClean()

    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    def toYes(self):
        self.select_op = True
        QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能已激活！！", )
    def toNo(self):
        self.select_op = False
        QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能已关闭！！", )
    def getClsNameLZ(self):

        if self.select_op:
            Pname = '👉冷轧👈'
            self.menus.select_name.setTitle(Pname)

            self.EngCls = ['BeiJing','ZhengMianQueXian','ErLeiTuoPi','ErLeiTuoPiYi','YiWuYaRu','XiuDian',
                           'BaHen','SuanYin','BianBuZhaXiu','TuoPi','BaoGuangSeCha','ReZhaGuaShang',
                           'YangHuaPiTuoLuoHen','TuiXiGuaShang','HeiDai','SuanXiBuZu','ReGunYin','ZangWu',
                           'AoKeng','BianSiLaRu','ZaoShang','TingJiWenLi','ZaoShangFenSuan','JianDuanReZhaGuaShang',
                           'SuanYinHuLue','XianXingJiaZa','YanZhongYangHuaPiTuoLuoHen','YaHen','YangHuaPiTuoLuoHenHuLue','HanFeng',
                           'CengJianCaShang','CengJianCaShangYi','ErLeiReZhaGuaShang','LieBian','ShuiYin','BianBuHuLue',
                           ]
            self.ChiCls = ['背景','整面缺陷','二类脱皮','二类脱皮一','异物压入','锈点',
                           '疤痕','酸印','边部轧锈','脱皮','曝光色差','热轧刮伤',
                           '氧化皮脱落痕','退洗刮伤','黑带','酸洗不足','热辊印','脏污',
                           '凹坑','边丝拉入','凿伤','停机纹理','凿伤分散','间断热轧刮伤',
                           '酸印忽略','线性夹杂','严重氧化皮脱落痕','压痕','氧化皮脱落痕忽略','焊缝',
                           '层间擦伤','层间擦伤一','二类热轧刮伤','裂边','水印','边部忽略',
                           ]
            self.labelDialog = LabelDialog(
                currentType='冷轧',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            #print("Pname_冷轧")
            self.select_op = False

        else:
            QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能失效,请点击激活按钮进行激活或选择打开目录进行激活！", )


    def getClsNameLZ_win(self,fuction_close):
        if self.select_op:
            Pname = '👉冷轧👈'
            self.menus.select_name.setTitle(Pname)

            self.EngCls = ['BeiJing','ZhengMianQueXian','ErLeiTuoPi','ErLeiTuoPiYi','YiWuYaRu','XiuDian',
                           'BaHen','SuanYin','BianBuZhaXiu','TuoPi','BaoGuangSeCha','ReZhaGuaShang',
                           'YangHuaPiTuoLuoHen','TuiXiGuaShang','HeiDai','SuanXiBuZu','ReGunYin','ZangWu',
                           'AoKeng','BianSiLaRu','ZaoShang','TingJiWenLi','ZaoShangFenSuan','JianDuanReZhaGuaShang',
                           'SuanYinHuLue','XianXingJiaZa','YanZhongYangHuaPiTuoLuoHen','YaHen','YangHuaPiTuoLuoHenHuLue','HanFeng',
                           'CengJianCaShang','CengJianCaShangYi','ErLeiReZhaGuaShang','LieBian','ShuiYin','BianBuHuLue',
                           ]
            self.ChiCls = ['背景','整面缺陷','二类脱皮','二类脱皮一','异物压入','锈点',
                           '疤痕','酸印','边部轧锈','脱皮','曝光色差','热轧刮伤',
                           '氧化皮脱落痕','退洗刮伤','黑带','酸洗不足','热辊印','脏污',
                           '凹坑','边丝拉入','凿伤','停机纹理','凿伤分散','间断热轧刮伤',
                           '酸印忽略','线性夹杂','严重氧化皮脱落痕','压痕','氧化皮脱落痕忽略','焊缝',
                           '层间擦伤','层间擦伤一','二类热轧刮伤','裂边','水印','边部忽略',
                           ]
            self.labelDialog = LabelDialog(
                currentType='冷轧',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            #print("Pname_冷轧")

            reply = QtWidgets.QMessageBox.question(self, '提示',
                                                   "当前选择产品类型为:<a style='color:red;font_size:1000'>冷轧</a>,确认请点击按钮 Yes,重新选型请点击按钮 No", QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.select_op = False
                fuction_close()


    def getClsNameRZ(self):

        if self.select_op:
            Pname = '👉热轧👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['DaiFenLei', 'JingZhaGunYin', 'DaiTouGunYin', 'ZhaLan', 'KongDong', 'ZhaRuWaiWu',
                           'BaoPian', 'JieBa', 'XianZhuangJiaZa', 'ZhuPiHuaShang', 'ZongXiangLieWen', 'GuaHen',
                           'LiangHuaShang', 'XiaFeng', 'YiCiXiuPi', 'ErCiXiuPi', 'TieLinYaRu', 'YangHuaTiePi',
                           'ZhenHen', 'PianZhuangTieLin', 'BoXing', 'ShuiDi', 'ShuiWu', 'ShuiYin',
                           'BaoGuangYinHen', 'TingZhiShuXian', 'BaiTieLin', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan',
                           'BeiJingSi', 'QiPi', 'TouWeiBian', 'BianYuanPoLie', 'BeiJingWu', 'BeiJingLiu',
                           'BianYuanMaoCi', 'GuoBaoGuang', 'XiuPiTuoLuo', 'CaBa', 'BeiJingQi', 'BeiJingBa',
                           'YiWuYaRu','TuBao','LaSiYaRu','ZongXiangHuaShang',
                           ]
            self.ChiCls = ['待分类', '精轧辊印', '带头辊印', '轧烂', '孔洞', '轧入外物',
                           '剥片', '结疤', '线状夹杂', '铸坯划伤', '纵向裂纹', '刮痕',
                           '亮划伤', '狭缝', '一次锈皮', '二次锈皮', '铁鳞压入', '氧化铁皮',
                           '振痕', '片状铁鳞', '波形', '水滴', '水雾', '水印',
                           '曝光印痕', '停止竖线', '白铁鳞', '背景一', '背景二', '背景三',
                           '背景四', '起皮', '头尾边', '边缘破裂', '背景五', '背景六',
                           '边缘毛刺', '过曝光', '锈皮脱落', '擦疤', '背景七', '背景八',
                           '异物压入','凸包','拉丝压入','纵向划伤',
                           ]
            self.labelDialog = LabelDialog(
                currentType='热轧',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            #print("Pname_热轧")
            self.select_op = False
        else:
            QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能失效,请点击激活按钮进行激活或选择打开目录进行激活！", )

    def getClsNameRZ_win(self,fuction_close):

        if self.select_op:
            Pname = '👉热轧👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['DaiFenLei', 'JingZhaGunYin', 'DaiTouGunYin', 'ZhaLan', 'KongDong', 'ZhaRuWaiWu',
                           'BaoPian', 'JieBa', 'XianZhuangJiaZa', 'ZhuPiHuaShang', 'ZongXiangLieWen', 'GuaHen',
                           'LiangHuaShang', 'XiaFeng', 'YiCiXiuPi', 'ErCiXiuPi', 'TieLinYaRu', 'YangHuaTiePi',
                           'ZhenHen', 'PianZhuangTieLin', 'BoXing', 'ShuiDi', 'ShuiWu', 'ShuiYin',
                           'BaoGuangYinHen', 'TingZhiShuXian', 'BaiTieLin', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan',
                           'BeiJingSi', 'QiPi', 'TouWeiBian', 'BianYuanPoLie', 'BeiJingWu', 'BeiJingLiu',
                           'BianYuanMaoCi', 'GuoBaoGuang', 'XiuPiTuoLuo', 'CaBa', 'BeiJingQi', 'BeiJingBa',
                           'YiWuYaRu', 'TuBao', 'LaSiYaRu', 'ZongXiangHuaShang',
                           ]
            self.ChiCls = ['待分类', '精轧辊印', '带头辊印', '轧烂', '孔洞', '轧入外物',
                           '剥片', '结疤', '线状夹杂', '铸坯划伤', '纵向裂纹', '刮痕',
                           '亮划伤', '狭缝', '一次锈皮', '二次锈皮', '铁鳞压入', '氧化铁皮',
                           '振痕', '片状铁鳞', '波形', '水滴', '水雾', '水印',
                           '曝光印痕', '停止竖线', '白铁鳞', '背景一', '背景二', '背景三',
                           '背景四', '起皮', '头尾边', '边缘破裂', '背景五', '背景六',
                           '边缘毛刺', '过曝光', '锈皮脱落', '擦疤', '背景七', '背景八',
                           '异物压入', '凸包', '拉丝压入', '纵向划伤',
                           ]
            self.labelDialog = LabelDialog(
                currentType='热轧',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            #print("Pname_热轧")
            reply = QtWidgets.QMessageBox.question(self, '提示',
                                                   "当前选择产品类型为:<a style='color:red;font_size:1000'>热轧</a>,确认请点击按钮 Yes,重新选型请点击按钮 No",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.select_op = False
                fuction_close()

    def getClsNameBC(self):

        if self.select_op:
            Pname = '👉板材👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['DaiFenLei', 'ZongXiangLieWen', 'HengXiangLieWen', 'BianLie', 'ShuiYin', 'GunYin',
                           'YaKeng', 'QiaoPi', 'XianXingQueXian', 'HuaShang', 'YaHen', 'ShuiDi',
                           'PingBiBianBu', 'PingBiTouWei', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan', 'BeiJingSi',
                           'BeiJingWu', 'BeiJingLiu', 'BeiJingQi', 'BeiJingBa', 'MaDian', 'YiWuYaRu',
                           'ShuiWen', 'JieBa', 'YangHuaTiePi', 'XianXingQueXianYi', 'YiSiYiWuYaRu',
                           ]
            self.ChiCls = ['待分类', '纵向裂纹', '横向裂纹', '边裂', '水印', '辊印',
                           '压坑', '翘皮', '线性缺陷', '划伤', '压痕', '水滴',
                           '屏蔽边部', '屏蔽头尾', '背景一', '背景二', '背景三', '背景四',
                           '背景五', '背景六', '背景七', '背景八', '麻点', '异物压入',
                           '水纹', '结疤', '氧化铁皮', '线性缺陷一', '疑似异物压入',
                           ]
            self.labelDialog = LabelDialog(
                currentType='板材',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            # print("Pname_板材")
            self.select_op = False
        else:
            QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能失效,请点击激活按钮进行激活或选择打开目录进行激活！", )

    def getClsNameBC_win(self,fuction_close):

        if self.select_op:
            Pname = '👉板材👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['DaiFenLei', 'ZongXiangLieWen', 'HengXiangLieWen', 'BianLie', 'ShuiYin', 'GunYin',
                           'YaKeng', 'QiaoPi', 'XianXingQueXian', 'HuaShang', 'YaHen', 'ShuiDi',
                           'PingBiBianBu', 'PingBiTouWei', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan', 'BeiJingSi',
                           'BeiJingWu', 'BeiJingLiu', 'BeiJingQi', 'BeiJingBa', 'MaDian', 'YiWuYaRu',
                           'ShuiWen', 'JieBa', 'YangHuaTiePi', 'XianXingQueXianYi', 'YiSiYiWuYaRu',
                           ]
            self.ChiCls = ['待分类', '纵向裂纹', '横向裂纹', '边裂', '水印', '辊印',
                           '压坑', '翘皮', '线性缺陷', '划伤', '压痕', '水滴',
                           '屏蔽边部', '屏蔽头尾', '背景一', '背景二', '背景三', '背景四',
                           '背景五', '背景六', '背景七', '背景八', '麻点', '异物压入',
                           '水纹', '结疤', '氧化铁皮', '线性缺陷一', '疑似异物压入',
                           ]
            self.labelDialog = LabelDialog(
                currentType='板材',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            # print("Pname_板材")
            reply = QtWidgets.QMessageBox.question(self, '提示',
                                                   "当前选择产品类型为:<a style='color:red;font_size:1000'>板材</a>,确认请点击按钮 Yes,重新选型请点击按钮 No",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.select_op = False
                fuction_close()

    def getClsNameCB(self):

        if self.select_op:
            Pname = '👉棒材👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['DaiFenLei', 'JingZhaGunYin', 'DaiTouGunYin', 'ZhaLan', 'KongDong', 'ZhaRuWaiWu',
                           'BaoPian', 'JieBa', 'XianZhuangJiaZa', 'ZhuPiHuaShang', 'ZongXiangLieWen', 'GuaHen',
                           'LiangHuaShang', 'XiaFeng', 'YiCiXiuPi', 'ErCiXiuPi', 'TieLinYaRu', 'YangHuaTiePi',
                           'ZhenHen', 'PianZhuangTieLin', 'BoXing', 'ShuiDi', 'ShuiWu', 'ShuiYin',
                           'BaoGuangYinHen', 'TingZhiShuXian', 'BaiTieLin', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan',
                           'BeiJingSi', 'QiPi', 'TouWeiBian', 'BianYuanPoLie', 'BeiJingWu', 'BeiJingLiu',
                           'BeiJingQi', 'BianYuanMaoCi', 'GuoBaoGuang', 'BeiJingBa', 'BeiJingJiu', 'BeiJingShi',
                           'BeiJingShiYi', 'XiuPiTuoLuo', 'AoKeng', 'ErDuo', 'HuaShang', 'BeiJing',
                           ]
            self.ChiCls = ['待分类', '精轧辊印', '带头辊印', '轧烂', '孔洞', '轧入外物',
                           '剥片', '结疤', '线状夹杂', '铸坯划伤', '纵向裂纹', '刮痕',
                           '亮划伤', '狭缝', '一次锈皮', '二次锈皮', '铁鳞压入', '氧化铁皮',
                           '振痕', '片状铁鳞', '波形', '水滴', '水雾', '水印',
                           '曝光印痕', '停止竖线', '白铁鳞', '背景一', '背景二', '背景三',
                           '背景四', '起皮', '头尾边', '边缘破裂', '背景五', '背景六',
                           '背景七', '边缘毛刺', '过曝光', '背景八', '背景九', '背景十',
                           '背景十一', '锈皮脱落', '凹坑', '耳朵', '划伤', '背景',
                           ]
            self.labelDialog = LabelDialog(
                currentType='棒材',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            # print("Pname_棒材")
            self.select_op =False
        else:
            QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能失效,请点击激活按钮进行激活或选择打开目录进行激活！", )

    def getClsNameCB_win(self,fuction_close):

        if self.select_op:
            Pname = '👉棒材👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['DaiFenLei', 'JingZhaGunYin', 'DaiTouGunYin', 'ZhaLan', 'KongDong', 'ZhaRuWaiWu',
                           'BaoPian', 'JieBa', 'XianZhuangJiaZa', 'ZhuPiHuaShang', 'ZongXiangLieWen', 'GuaHen',
                           'LiangHuaShang', 'XiaFeng', 'YiCiXiuPi', 'ErCiXiuPi', 'TieLinYaRu', 'YangHuaTiePi',
                           'ZhenHen', 'PianZhuangTieLin', 'BoXing', 'ShuiDi', 'ShuiWu', 'ShuiYin',
                           'BaoGuangYinHen', 'TingZhiShuXian', 'BaiTieLin', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan',
                           'BeiJingSi', 'QiPi', 'TouWeiBian', 'BianYuanPoLie', 'BeiJingWu', 'BeiJingLiu',
                           'BeiJingQi', 'BianYuanMaoCi', 'GuoBaoGuang', 'BeiJingBa', 'BeiJingJiu', 'BeiJingShi',
                           'BeiJingShiYi', 'XiuPiTuoLuo', 'AoKeng', 'ErDuo', 'HuaShang', 'BeiJing',
                           ]
            self.ChiCls = ['待分类', '精轧辊印', '带头辊印', '轧烂', '孔洞', '轧入外物',
                           '剥片', '结疤', '线状夹杂', '铸坯划伤', '纵向裂纹', '刮痕',
                           '亮划伤', '狭缝', '一次锈皮', '二次锈皮', '铁鳞压入', '氧化铁皮',
                           '振痕', '片状铁鳞', '波形', '水滴', '水雾', '水印',
                           '曝光印痕', '停止竖线', '白铁鳞', '背景一', '背景二', '背景三',
                           '背景四', '起皮', '头尾边', '边缘破裂', '背景五', '背景六',
                           '背景七', '边缘毛刺', '过曝光', '背景八', '背景九', '背景十',
                           '背景十一', '锈皮脱落', '凹坑', '耳朵', '划伤', '背景',
                           ]
            self.labelDialog = LabelDialog(
                currentType='棒材',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            # print("Pname_棒材")
            reply = QtWidgets.QMessageBox.question(self, '提示',
                                                   "当前选择产品类型为:<a style='color:red;font_size:1000'>棒材</a>,确认请点击按钮 Yes,重新选型请点击按钮 No",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.select_op = False
                fuction_close()

    #铸坯
    def getClsNameZP(self):

        if self.select_op:
            Pname = '👉铸坯👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['BeiJing', 'ZongXiangLieWen', 'HengXiangLieWen', 'HuaShang', 'ShuiZhaYin', 'GunYin',
                           'ZhaPi', 'QieGeKaiKou', 'TingZhiXian', 'CaHuaShang', 'DuanMianHanZha', 'JieHen',
                           ]
            self.ChiCls = ['背景', '纵向裂纹', '横向裂纹', '划伤', '水渣印', '辊印',
                           '渣皮', '切割开口', '停止线', '擦划伤', '端面焊渣', '接痕',
                           ]
            self.labelDialog = LabelDialog(
                currentType='铸坯',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            self.select_op = False
        else:
            QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能失效,请点击激活按钮进行激活或选择打开目录进行激活！", )

    def getClsNameZP_win(self,fuction_close):

        if self.select_op:
            Pname = '👉铸坯👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['BeiJing', 'ZongXiangLieWen', 'HengXiangLieWen', 'HuaShang', 'ShuiZhaYin', 'GunYin',
                           'ZhaPi', 'QieGeKaiKou', 'TingZhiXian', 'CaHuaShang', 'DuanMianHanZha', 'JieHen',
                           ]
            self.ChiCls = ['背景', '纵向裂纹', '横向裂纹', '划伤', '水渣印', '辊印',
                           '渣皮', '切割开口', '停止线', '擦划伤', '端面焊渣', '接痕',
                           ]
            self.labelDialog = LabelDialog(
                currentType='铸坯',
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )

            reply = QtWidgets.QMessageBox.question(self, '提示',
                                                   "当前选择产品类型为:<a style='color:red;font_size:1000'>铸坯</a>,确认请点击按钮 Yes,重新选型请点击按钮 No",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.select_op = False
                fuction_close()
    def getClsNameZF(self):

        if self.select_op:
            Pname = '👉字符👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['BeiJing','0','1','2','3','4','5','6','7','8','9',
                              'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                              'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                              '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                              'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                              'u','v','w','x','y','z']
            self.ChiCls = ['背景','0','1','2','3','4','5','6','7','8','9',
                              'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                              'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                              '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                              'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                              'u','v','w','x','y','z']
            self.labelDialog = LabelDialog(
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            # print("Pname_字符")
            # print(self.EngCls)
            # print(self.ChiCls)
            self.select_op = False
        else:
            QtWidgets.QMessageBox.information(self, '提示', "切换产品类型功能失效,请点击激活按钮进行激活或选择打开目录进行激活！", )

    def getClsNameZF_win(self,fuction_close):

        if self.select_op:
            Pname = '👉字符👈'
            self.menus.select_name.setTitle(Pname)
            self.EngCls = ['BeiJing','0','1','2','3','4','5','6','7','8','9',
                              'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                              'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                              '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                              'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                              'u','v','w','x','y','z']
            self.ChiCls = ['背景','0','1','2','3','4','5','6','7','8','9',
                              'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                              'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                              '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                              'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                              'u','v','w','x','y','z']
            self.labelDialog = LabelDialog(
                parent=self,
                labels=self._config["labels"],
                sort_labels=self._config["sort_labels"],
                show_text_field=self._config["show_label_text_field"],
                completion=self._config["label_completion"],
                fit_to_content=self._config["fit_to_content"],
                flags=self._config["label_flags"],
                EngClsList = self.EngCls,
                ChiClsList = self.ChiCls,
            )
            # print("Pname_字符")
            reply = QtWidgets.QMessageBox.question(self, '提示',
                                                   "当前选择产品类型为:<a style='color:red;font_size:1000'>字符</a>,确认请点击按钮 Yes,重新选型请点击按钮 No",
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.select_op = False
                fuction_close()
    def getLabelFile(self):
        if self.filename.lower().endswith(".json"):
            label_file = self.filename
        else:
            label_file = osp.splitext(self.filename)[0] + ".json"

        return label_file

    def deleteFile(self):
        mb = QtWidgets.QMessageBox
        msg = self.tr(
            "You are about to permanently delete this label file, "
            "proceed anyway?"
        )
        answer = mb.warning(self, self.tr("Attention"), msg, mb.Yes | mb.No)
        if answer != mb.Yes:
            return

        label_file = self.getLabelFile()
        if osp.exists(label_file):
            os.remove(label_file)
            logger.info("Label file is removed: {}".format(label_file))

            item = self.fileListWidget.currentItem()
            item.setCheckState(Qt.Unchecked)

            self.resetState()

    # Message Dialogs. #
    def hasLabels(self):
        if self.noShapes():
            self.errorMessage(
                "No objects labeled",
                "You must label at least one object to save the file.",
            )
            return False
        return True

    def hasLabelFile(self):
        if self.filename is None:
            return False

        label_file = self.getLabelFile()
        return osp.exists(label_file)

    def mayContinue(self):
        if not self.dirty:
            return True
        mb = QtWidgets.QMessageBox
        msg = self.tr('Save annotations to "{}" before closing?').format(
            self.filename
        )
        answer = mb.question(
            self,
            self.tr("Save annotations?"),
            msg,
            mb.Save | mb.Discard | mb.Cancel,
            mb.Save,
        )
        if answer == mb.Discard:
            return True
        elif answer == mb.Save:
            self.saveFile()
            return True
        else:  # answer == mb.Cancel
            return False

    def errorMessage(self, title, message):
        return QtWidgets.QMessageBox.critical(
            self, title, "<p><b>%s</b></p>%s" % (title, message)
        )

    def currentPath(self):
        return osp.dirname(str(self.filename)) if self.filename else "."

    def toggleKeepPrevMode(self):
        self._config["keep_prev"] = not self._config["keep_prev"]

    def removeSelectedPoint(self):
        self.canvas.removeSelectedPoint()
        if not self.canvas.hShape.points:
            self.canvas.deleteShape(self.canvas.hShape)
            self.remLabels([self.canvas.hShape])
            self.setDirty()
            #print('已进入setDirty函数6')
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)

    def deleteSelectedShape(self):
        yes, no = QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No
        msg = self.tr(
            "You are about to permanently delete {} polygons, "
            "proceed anyway?"
        ).format(len(self.canvas.selectedShapes))
        if yes == QtWidgets.QMessageBox.warning(
            self, self.tr("Attention"), msg, yes | no, yes
        ):
            self.remLabels(self.canvas.deleteSelected())
            self.setDirty()
            #print('已进入setDirty函数7')
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)

    def copyShape(self):
        # print('进入copyShape')
        self.canvas.endMove(copy=True)
        self.labelList.clearSelection()
        for shape in self.canvas.selectedShapes:
            self.addLabel(shape)
        self.setDirty()
        #print('已进入setDirty函数8')

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()
        #print('已进入setDirty函数9')

    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return

        defaultOpenDirPath = dirpath if dirpath else "."
        if self.lastOpenDir and osp.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = (
                osp.dirname(self.filename) if self.filename else "."
            )
        targetDirPath = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.tr("%s - Open Directory") % __appname__,
                defaultOpenDirPath,
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
        )

        if targetDirPath and self.mode ==1:
            self.select_op = True
            product_type = self.childSSS
            product_type.setModal(True)
            product_type.showwin(self.importDirImages,targetDirPath)
            # self.select_op = False
            # self.importDirImages(targetDirPath)
        if targetDirPath and self.mode ==2:
            self.importDirImages(targetDirPath)
            if self.select_op is False:
                self.select_op = True
                QtWidgets.QMessageBox.information(self, '提示', "产品切换功能已激活！！！", )

    @property
    def imageList(self):
        lst = []
        for i in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(i)
            lst.append(item.text())
        return lst

    def importDroppedImageFiles(self, imageFiles):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]

        self.filename = None
        for file in imageFiles:
            if file in self.imageList or not file.lower().endswith(
                tuple(extensions)
            ):
                continue
            label_file = osp.splitext(file)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(file)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                label_file
            ):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.fileListWidget.addItem(item)

        if len(self.imageList) > 1:
            self.actions.openNextImg.setEnabled(True)
            self.actions.openPrevImg.setEnabled(True)

        self.openNextImg()

    def importDirImages(self, dirpath, pattern=None, load=True):
        self.actions.openNextImg.setEnabled(True)
        self.actions.openPrevImg.setEnabled(True)

        if not self.mayContinue() or not dirpath:
            return

        self.lastOpenDir = dirpath
        self.filename = None
        self.fileListWidget.clear()
        for filename in self.scanAllImages(dirpath):
            if pattern and pattern not in filename:
                continue
            label_file = osp.splitext(filename)[0] + ".json"
            if self.output_dir:
                label_file_without_path = osp.basename(label_file)
                label_file = osp.join(self.output_dir, label_file_without_path)
            item = QtWidgets.QListWidgetItem(filename)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                label_file
            ):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.fileListWidget.addItem(item)
        self.openNextImg(load=load)

    def scanAllImages(self, folderPath):
        extensions = [
            ".%s" % fmt.data().decode().lower()
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]

        images = []
        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = osp.join(root, file)
                    images.append(relativePath)
        images.sort(key=lambda x: x.lower())
        return images


class select_product_type(QtWidgets.QDialog):
    def __init__(self,LZ,RZ,BC,CB,ZP,ZF): #LZ,RZ,BC,CB,ZP,ZF
        super().__init__()
        self.useLz = LZ
        self.useRz = RZ
        self.useBc = BC
        self.useCb = CB
        self.useZp = ZP
        self.useZf = ZF
        self.initUI()

    def closewin(self):
        self.close()
        self.file_f(self.path)
    def showwin(self,op_f,path):
        self.file_f = op_f
        self.path = path
        self.show()


    def initUI(self):
        # 创建一个菜单
        self.MenuBtn = QtWidgets.QPushButton("产品类型", self)

        # 创建一个菜单对象
        self.Menu = QtWidgets.QMenu()
        # 菜单中的选项
        lz_action = QtWidgets.QAction('冷轧', self)  # 创建对象
        lz_action.triggered.connect(lambda :self.useLz(self.closewin))
        rz_action = QtWidgets.QAction('热轧', self)  # 创建对象
        rz_action.triggered.connect(lambda:self.useRz(self.closewin))
        bc_action = QtWidgets.QAction('板材', self)  # 创建对象
        bc_action.triggered.connect(lambda:self.useBc(self.closewin))
        cb_action = QtWidgets.QAction('棒材', self)  # 创建对象
        cb_action.triggered.connect(lambda:self.useCb(self.closewin))
        zp_action = QtWidgets.QAction('铸坯', self)  # 创建对象
        zp_action.triggered.connect(lambda:self.useZp(self.closewin))
        zf_action = QtWidgets.QAction('字符', self)  # 创建对象
        zf_action.triggered.connect(lambda:self.useZf(self.closewin))

        self.Menu.addActions([lz_action, rz_action, bc_action, cb_action, zp_action,zf_action])  # 将图标添加到菜单中
        self.MenuBtn.setMenu(self.Menu)  # 将菜单添加到按键中
        self.label1 = QtWidgets.QLabel('请选择产品类型:', self)
        # self.btno = QtWidgets.QPushButton("确定", self)
        # self.btno.clicked.connect(self.closewin)

        self.setGeometry(400, 400, 200, 50)
        self.setWindowTitle('标注工具[测试版本v1.0.0]:BKVISION')
        self.MenuBtn.move(self.MenuBtn.height()//2+0.9*self.MenuBtn.width(), self.height() // 5)
        self.label1.resize(self.MenuBtn.width(),self.MenuBtn.height())
        self.label1.move(self.MenuBtn.x()-0.9*self.label1.width(),self.MenuBtn.y()-3)
        # self.btno.move(self.MenuBtn.x()+self.MenuBtn.width(),self.MenuBtn.y())
        # 固定窗口大小
        # self.setFixedSize(self.width(), self.height())

        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.MSWindowsFixedSizeDialogHint)
