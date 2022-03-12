import argparse
import codecs
import json
import logging
import os
import os.path as osp
import sys
import platform
import qtpy
import yaml
import time
import glob
import cv2
import imgviz
import json
import shutil
import base64
from threading import Thread
from Crypto.Cipher import AES
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom.minidom import Document
from PIL import Image,ImageDraw
from qtpy import QtCore
from qtpy import QtWidgets
from skimage import img_as_ubyte
from labelme import __appname__
from labelme import __version__
from labelme.app import MainWindow
from labelme.config import get_config
from labelme.logger import logger
from labelme.utils import newIcon


# str不是16的倍数那就补足为16的倍数
def add_to_16(value):
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)  # 返回byte

def decrypt_ase(path):
    # 秘钥
    key = 'Nercar701'
    # 密文
    with open(path, 'r', encoding='utf-8') as banks:
        text = banks.read()
    # 初始化加密器
    aes = AES.new(add_to_16(key), AES.MODE_ECB)
    # 优先逆向解密base64成bytes
    base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
    # bytes解密
    decrypted_text = str(aes.decrypt(base64_decrypted),encoding='utf-8') # 执行解密密并转码返回str
    decrypted_text = base64.b64decode(decrypted_text.encode('utf-8')).decode('utf-8')
    return json.loads(decrypted_text)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", "-V", action="store_true", help="show version"
    )
    parser.add_argument(
        "--reset-config", action="store_true", help="reset qt config"
    )
    parser.add_argument(
        "--logger-level",
        default="info",
        choices=["debug", "info", "warning", "fatal", "error"],
        help="logger level",
    )
    parser.add_argument("filename", nargs="?", help="image or label filename")
    parser.add_argument(
        "--output",
        "-O",
        "-o",
        help="output file or directory (if it ends with .json it is "
        "recognized as file, else as directory)",
    )
    default_config_file = os.path.join(os.path.expanduser("~"), ".labelmerc")
    parser.add_argument(
        "--config",
        dest="config",
        help="config file or yaml-format string (default: {})".format(
            default_config_file
        ),
        default=default_config_file,
    )
    # config for the gui
    parser.add_argument(
        "--nodata",
        dest="store_data",
        action="store_false",
        help="stop storing image data to JSON file",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--autosave",
        dest="auto_save",
        action="store_true",
        help="auto save",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--nosortlabels",
        dest="sort_labels",
        action="store_false",
        help="stop sorting labels",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--flags",
        help="comma separated list of flags OR file containing flags",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--labelflags",
        dest="label_flags",
        help=r"yaml string of label specific flags OR file containing json "
        r"string of label specific flags (ex. {person-\d+: [male, tall], "
        r"dog-\d+: [black, brown, white], .*: [occluded]})",  # NOQA
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--labels",
        help="comma separated list of labels OR file containing labels",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--validatelabel",
        dest="validate_label",
        choices=["exact"],
        help="label validation types",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--keep-prev",
        action="store_true",
        help="keep annotation of previous frame",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        help="epsilon to find nearest vertex on canvas",
        default=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.version:
        print("{0} {1}".format(__appname__, __version__))
        sys.exit(0)

    #获取logging对象中的属性:args.logger_level.upper() getattr
    logger.setLevel(getattr(logging, args.logger_level.upper()))
    #hasattr() 函数用于判断对象是否包含对应的属性。
    if hasattr(args, "flags"):
        if os.path.isfile(args.flags):
            with codecs.open(args.flags, "r", encoding="utf-8") as f:
                args.flags = [line.strip() for line in f if line.strip()]
        else:
            args.flags = [line for line in args.flags.split(",") if line]

    if hasattr(args, "labels"):
        if os.path.isfile(args.labels):
            with codecs.open(args.labels, "r", encoding="utf-8") as f:
                args.labels = [line.strip() for line in f if line.strip()]
        else:
            args.labels = [line for line in args.labels.split(",") if line]

    if hasattr(args, "label_flags"):
        if os.path.isfile(args.label_flags):
            with codecs.open(args.label_flags, "r", encoding="utf-8") as f:
                args.label_flags = yaml.safe_load(f)
        else:
            args.label_flags = yaml.safe_load(args.label_flags)

    config_from_args = args.__dict__
    config_from_args.pop("version")
    reset_config = config_from_args.pop("reset_config")
    filename = config_from_args.pop("filename")
    output = config_from_args.pop("output")
    config_file_or_yaml = config_from_args.pop("config")
    config = get_config(config_file_or_yaml, config_from_args)

    if not config["labels"] and config["validate_label"]:
        logger.error(
            "--labels must be specified with --validatelabel or "
            "validate_label: true in the config file "
            "(ex. ~/.labelmerc)."
        )
        sys.exit(1)

    output_file = None
    output_dir = None
    if output is not None:
        if output.endswith(".json"):
            output_file = output
        else:
            output_dir = output

    # 汉化
    # translator = QtCore.QTranslator()
    # translator.load(
    #     QtCore.QLocale.system().name(),
    #     osp.dirname(osp.abspath(__file__)) + "/translate",
    # )
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon("icon"))
    # 汉化
    # app.installTranslator(translator)
    #解密文件得到钢种缺陷类别信息
    try:
        class_names = decrypt_ase('bankdata.bin')
    except:
        QtWidgets.QMessageBox.warning(QtWidgets.QMainWindow(),'错误', f"缺少.bin文件,请检查当前目录{os.getcwd()}")
        sys.exit()


    #标注窗口
    win = MainWindow(
        class_dict=class_names,
        config=config,
        filename=filename,
        output_file=output_file,
        output_dir=output_dir,
        mode=1,
    )

    if reset_config:
        logger.info("Resetting Qt config: %s" % win.settings.fileName())
        win.settings.clear()
        sys.exit(0)

    #
    class First(QtWidgets.QMainWindow):
        def __init__(self,win,class_names):
            super().__init__()
            self.win = win
            self.class_info_dict = class_names
            self.get_directory_path = None
            self.initUI()

        def closewin(self):
            self.close()

        def switchWin(self):
            self.closewin()
            self.win.show()
            self.win.raise_()

        def isInZh(self,s):
            for c in s:
                if '\u4e00' <= c <= '\u9fa5':
                    return True
            return False

        def openFile(self):
            self.get_directory_path = QtWidgets.QFileDialog.getExistingDirectory(self,"选取指定文件夹","C:/")

        def check_file(self,name):
            if os.path.exists(name):
                while True:
                    try:
                        shutil.rmtree(name)
                        os.makedirs(name)
                        break
                    except:
                        time.sleep(0.5)
                        continue
            else:
                os.makedirs(name)

        def del_dir(self,name):
            if os.path.exists(name):
                while True:
                    try:
                        shutil.rmtree(name)
                        break
                    except:
                        time.sleep(0.5)
                        continue

        def chackPath(self):
            DataPath = self.get_directory_path
            if not DataPath:
                QtWidgets.QMessageBox.warning(self, '错误', "请选择非空目录！！", )
                return None,None, None
            elif not ("images" and "labels") in os.listdir(DataPath):
                QtWidgets.QMessageBox.warning(self, '错误', "请选择包含images和labels的目录！！", )
                return None, None, None
            else:
                JsonPaths = os.path.join(DataPath,"labels")
                ImgPaths = os.path.join(DataPath,"images")
                Ptyoe = DataPath.split('/')[-2]
                return JsonPaths,ImgPaths,Ptyoe

        def GenClsData(self):
            JsonPaths,ImgPaths,PType = self.chackPath()
            if not JsonPaths or not ImgPaths:
                return
            if "板" in PType:
                EngCls = self.class_info_dict['板材']['英文']
            elif "棒" in PType:
                EngCls = self.class_info_dict['棒材']['英文']
            elif "铸" in PType:
                EngCls = self.class_info_dict['铸坯']['英文']
            elif "冷" in PType:
                EngCls = self.class_info_dict['冷轧']['英文']
            elif "热" in PType:
                EngCls = self.class_info_dict['热轧']['英文']
            elif "符" in PType:
                EngCls = self.class_info_dict['字符']['英文']
            else:
                QtWidgets.QMessageBox.warning(self, '错误', "请选择支持的产品类型样本集！！", )
                return
            Save_dir = JsonPaths.replace('labels', 'ClassifiedData')
            self.check_file(Save_dir)
            total_num = len(os.listdir(JsonPaths))
            image_index = 0
            bk = 0
            for JsonPath in glob.glob(JsonPaths+"/*.json"):
                ImagePath = JsonPath.replace('json','bmp').replace('labels','images')
                #print(ImagePath)
                if not os.path.exists(ImagePath):
                    ImagePath = JsonPath.replace('json','jpg').replace('labels','images')
                if not os.path.exists(ImagePath):
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    QtWidgets.QMessageBox.information(self, '提示', f"图片:{ImgName}.??? 不存在或者格式为非bmp、jpg! 点击OK键继续！", )
                    bk += 1
                if bk >= 1:
                    image_index += 1
                    self.pbar.setValue(image_index / total_num * 100)
                    QtWidgets.QApplication.processEvents()
                    continue

                if platform.system() =="Windows":
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    ImgMat = ImagePath.split('\\')[-1].split('.')[1]
                elif platform.system() =="Linux":
                    ImgName = ImagePath.split('/')[-1].split('.')[0]
                    ImgMat = ImagePath.split('/')[-1].split('.')[1]

                ImgSrc = Image.open(ImagePath).convert('L')
                ImgW, ImgH = ImgSrc.size
                data = json.load(open(JsonPath,'r',encoding='utf8'))
                shapeList = data['shapes']
                #print(shapeList)
                Roi_index = 1
                for shape in shapeList:
                    points = shape['points']
                    className = shape["chineselabel"]
                    eng_name = shape["label"]
                    if str(eng_name) not in EngCls:
                        QtWidgets.QMessageBox.information(self, '提示', f"类别{className}:不属于当前{PType}类型类别! 点击OK继续！！！")
                        continue
                    print(Save_dir,className,eng_name,str(eng_name) not in EngCls)
                    print(ImagePath)
                    Subfolder = os.path.join(Save_dir, className)
                    Roi_path = os.path.join(Subfolder, ImgName + "_" + str(Roi_index) + f".{ImgMat}")
                    if shape['shape_type'] == 'rectangle':
                        if not os.path.exists(Subfolder):
                            os.makedirs(Subfolder)
                        x1, y1, x2, y2 = (points[0][0],points[0][1],points[1][0],points[1][1])
                        x1_temp = min(x1,x2)-100
                        y1_temp = min(y1,y1)-100
                        x2_temp = max(x1,x2)+100
                        y2_temp = max(y1,y1)+100
                        if x1_temp <= 0:
                            x1_temp = 0
                        if x2_temp >= ImgW:
                            x2_temp = ImgW
                        if y1_temp <= 0:
                            y1_temp = 0
                        if y2_temp >=ImgH:
                            y2_temp = ImgH
                        x1,y1,x2,y2 = x1_temp,y1_temp,x2_temp,y2_temp
                        Roi_pil = ImgSrc.crop((x1,y1,x2,y2))
                        Roi_pil.save(Roi_path)
                        Roi_index += 1
                    elif shape['shape_type']=='polygon':
                        if not os.path.exists(Subfolder):
                            os.makedirs(Subfolder)

                        x,y,w,h = cv2.boundingRect(np.array(points).astype('int'))
                        x1,y1,x2,y2 = x-100,y-100,x+w+100,y+h+100
                        if x1 <= 0:
                            x1 = 0
                        if x2 >= ImgW:
                            x2 = ImgW
                        if y1 <= 0:
                            y1 = 0
                        if y2 >=ImgH:
                            y2 = ImgH
                        Roi_pil = ImgSrc.crop((x1,y1,x2,y2))
                        Roi_pil.save(Roi_path)
                        Roi_index += 1

                    else:
                        reply = QtWidgets.QMessageBox.question(self, '提示',
                                                               "暂不支持多边形之外的类型，是否过滤并继续？", QtWidgets.QMessageBox.Yes |
                                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                        if reply ==QtWidgets.QMessageBox.Yes:
                            continue
                        else:
                            break
                image_index +=1
                self.pbar.setValue(image_index / total_num * 100)
                QtWidgets.QApplication.processEvents()
                # time.sleep(0.05)

        def GenSegData(self):
            JsonPaths, ImgPaths,PType = self.chackPath()
            if not JsonPaths or not ImgPaths:
                return
            Save_dir = JsonPaths.replace('labels', 'SegmentationData')
            save_img_dir = os.path.join(Save_dir,"SegImages")
            save_msk_dir = os.path.join(Save_dir,"SegLabels")
            save_msk_dir_rgb = os.path.join(Save_dir,"RGBSegLabels")
            self.check_file(save_img_dir)
            self.check_file(save_msk_dir)
            self.check_file(save_msk_dir_rgb)
            # if not os.path.exists(save_img_dir):
            #     os.makedirs(save_img_dir)
            # if not os.path.exists(save_msk_dir):
            #     os.makedirs(save_msk_dir)
            # if not os.path.exists(save_msk_dir_rgb):
            #     os.makedirs(save_msk_dir_rgb)
            if "板" in PType:
                EngCls = self.class_info_dict['板材']['英文']
            elif "棒" in PType:
                EngCls = self.class_info_dict['棒材']['英文']
            elif "铸" in PType:
                EngCls = self.class_info_dict['铸坯']['英文']
            elif "冷" in PType:
                EngCls = self.class_info_dict['冷轧']['英文']
            elif "热" in PType:
                EngCls = self.class_info_dict['热轧']['英文']
            elif "符" in PType:
                EngCls = self.class_info_dict['字符']['英文']
            else:
                QtWidgets.QMessageBox.warning(self, '错误', "请选择支持的产品类型样本集！！", )
                return
            info ={}
            info["classnames"] = EngCls
            with open(os.path.join(Save_dir,'classnames.json'),'w',encoding='utf8') as f:
                json.dump(info,f,indent=4,separators=(',', ': '))

            total_num = len(os.listdir(JsonPaths))
            image_index = 0
            for JsonPath in glob.glob(JsonPaths + "/*.json"):
                bk = 0
                ImagePath = JsonPath.replace('json', 'bmp').replace('labels', 'images')
                if not os.path.exists(ImagePath):
                    ImagePath = JsonPath.replace('json', 'jpg').replace('labels', 'images')
                if not os.path.exists(ImagePath):
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    QtWidgets.QMessageBox.information(self, '提示', f"图片:{ImgName}.??? 不存在或者格式为非bmp、jpg! 点击OK键继续！", )
                    bk += 1
                if bk >= 1:
                    image_index += 1
                    self.pbar.setValue(image_index / total_num * 100)
                    QtWidgets.QApplication.processEvents()
                    continue
                MskMat = 'png'
                if platform.system() == "Windows":
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    ImgMat = ImagePath.split('\\')[-1].split('.')[1]
                elif platform.system() == "Linux":
                    ImgName = ImagePath.split('/')[-1].split('.')[0]
                    ImgMat = ImagePath.split('/')[-1].split('.')[1]
                ImagePIL = Image.open(ImagePath).convert('L') #w,h
                data = json.load(open(JsonPath, 'r', encoding='utf8'))
                mask_label = np.zeros(ImagePIL.size[::-1][:2], dtype=np.uint8)  # w,h
                shapeList = data['shapes']
                flag = 0
                # print('ImagePath：',ImagePath)
                for shape in shapeList:
                    mask = np.zeros(ImagePIL.size[::-1][:2], dtype=np.uint8)  # w,h
                    mask = Image.fromarray(mask)
                    if shape['shape_type'] == 'polygon':
                        flag += 1
                        points = shape['points']
                        className = shape["label"]
                        if str(className) not in EngCls:
                            QtWidgets.QMessageBox.information(self, '提示', f"类别{className}:不属于当前{PType}类型类别! 点击OK继续！！！")
                            continue
                        classIndex = EngCls.index(className)
                        # print('classIndex:',classIndex,'className:',className)
                        xy = list(map(tuple, points))
                        ImageDraw.Draw(mask).polygon(xy=xy, outline=1, fill=1)
                        mask_bool = np.array(mask,dtype=bool)
                        mask_label[mask_bool]=classIndex
                if flag != 0:
                    mask_label=img_as_ubyte(mask_label) #0-255
                    mask_label_rgb= imgviz.label2rgb(mask_label)
                    new_img_path = os.path.join(save_img_dir,ImgName+f'.{ImgMat}')
                    mask_label_path = os.path.join(save_msk_dir,ImgName+f'.{MskMat}')
                    mask_label_path_rgb = os.path.join(save_msk_dir_rgb,ImgName+f'.{MskMat}')
                    if total_num == 1:
                        if os.path.exists(new_img_path):
                            os.remove(new_img_path)
                        if os.path.exists(mask_label_path):
                            os.remove(mask_label_path)
                        if os.path.exists(mask_label_path_rgb):
                            os.remove(mask_label_path_rgb)
                    ImagePIL.save(new_img_path)
                    Image.fromarray(mask_label).save(mask_label_path)
                    Image.fromarray(mask_label_rgb).save(mask_label_path_rgb)
                image_index += 1
                self.pbar.setValue(image_index / total_num * 100)
                QtWidgets.QApplication.processEvents()
                # time.sleep(0.05)

        def GenVOCDate(self):
            self.GetBBox(mold="VOC")

        def GenYOLODate(self):
            self.GetBBox(mold="YOLO")

        def clip_img(self,
                     img_path, img_name, img_mat,
                     label_path,label_mat ,
                     EngCls, mode,
                     imgs_save_dir, labels_save_dir,
                     save_img_dir_back,save_Ann_dir_back,
                     debug=False):

            ImagePIL = Image.open(img_path).convert('L')  # w,h
            img = np.array(ImagePIL)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            h_ori, w_ori = img.shape  # 保存原图的大小
            # print(f'{img_path}:::{img.shape}')
            # img = cv2.resize(img, (2048, 2048))#可以resize也可以不resize，看情况而定
            h, w = img.shape
            # 读取每个原图像的json文件
            data = json.load(open(label_path, 'r', encoding='utf8'))
            shapeList = data['shapes']
            res = np.empty((0, 5))  # 存放坐标的四个值和类别
            for shape in shapeList:
                if shape['shape_type'] == 'rectangle':
                    points = shape['points']
                    x1, y1, x2, y2 = points[0][0], points[0][1], points[1][0], points[1][1]
                    x1_tmp = min(x1, x2)*(w/w_ori)
                    y1_tmp = min(y1, y2)*(h/h_ori)
                    x2_tmp = max(x1, x2)*(w/w_ori)
                    y2_tmp = max(y1, y2)*(h/h_ori)
                    x1, y1, x2, y2 = x1_tmp-1, y1_tmp-1, x2_tmp-1, y2_tmp-1
                    className = shape["label"]
                    if str(className) not in EngCls:
                        continue
                    res = np.vstack((res, [int(x1), int(y1), int(x2), int(y2), className]))

            if res.shape[0] == 0:
                if not os.path.exists(save_img_dir_back):
                    os.makedirs(save_img_dir_back)
                if not os.path.exists(save_Ann_dir_back):
                    os.makedirs(save_Ann_dir_back)
                img_save_path_2 = os.path.join(save_img_dir_back,img_name+f".{img_mat}")
                lal_save_path_2 = os.path.join(save_Ann_dir_back,img_name+f".{label_mat}")
                ImagePIL.save(img_save_path_2)
                lbl_file = open(lal_save_path_2, 'wb+', encoding='utf8')
                lbl_file.close()
                return

            i = 0
            w_win_size = 1024
            h_win_size = h
            stride = 1024 - 256  # 重叠的大小（768），设置这个可以使分块有重叠  stride =win_size 说明设置的分块没有重叠
            for r in range(0, (h - h_win_size) + 1, stride):  # H方向进行切分
                for c in range(0, (w - w_win_size) + 1, stride):  # W方向进行切分
                    flag = np.zeros([1, len(res)])  # 修改flag = np.zeros([1, len(res)])
                    youwu = False  # 是否有物体
                    xiefou = True  # 是否记录

                    tmp = img[r: r + h_win_size, c: c + w_win_size]
                    tmp_PIL = Image.fromarray(tmp)
                    if debug:
                        tmp_cr = np.random.randint(0, 255, 3, np.uint8)
                        rgb_cr = (int(tmp_cr[0]), int(tmp_cr[1]), int(tmp_cr[2]))
                        cv2.rectangle(img_rgb, (c, r), (c + w_win_size, r + h_win_size), rgb_cr, 2)
                        cv2.namedWindow('haha', 0)
                        cv2.imshow('haha', img_rgb)
                        cv2.waitKey()
                    i = i + 1
                    #print(f'高度{r}', f'宽度{c}', f'切分图像尺寸：{tmp.shape}')
                    # 存储切分区域内框的信息
                    temp_boxes = []
                    # 遍历每一个框
                    for re in range(res.shape[0]):
                        xmin, ymin, xmax, ymax, label = res[re]
                        # 如果坐标异常，进行坐标转换
                        if int(xmin) > int(xmax):
                            xmin, xmax = xmax, xmin
                        if int(ymin) > int(ymax):
                            ymin, ymax = ymax, ymin

                        # 切分区域切中标注框，进行修正
                        # 1,剪裁区域左边界将box切分
                        if int(xmin) < c < int(xmax):
                            xmin = c + 1
                        # 2,剪裁区域右边界将box切分
                        if int(xmax) > c + w_win_size > int(xmin):
                            xmax = c + w_win_size - 1
                        # 3,剪裁区域上边界将box切分
                        if int(ymin) < r < int(ymax):
                            ymin = r + 1
                        # 4，剪裁区域下边界将box切分
                        if int(ymax) > r + h_win_size > int(ymin):
                            ymax = r + h_win_size - 1

                        # 如果坐标离谱(包含处理前和原生标注框信息)，跳出遍历框的循环
                        if int(xmin) == int(xmax) or int(ymin) == int(ymax):
                            xiefou = False
                            break

                        # 如果框完全在切分图中
                        if int(xmin) >= c and int(xmax) <= c + w_win_size and int(ymin) >= r and int(
                                ymax) <= r + h_win_size:
                            flag[0][re] = 1  # 用于判断是第几个bbox坐标信息在该小图中
                            x1 = int(xmin)-c
                            y1 = int(ymin)-r
                            x2 = int(xmax)-c
                            y2 = int(ymax)-r
                            temp_boxes.append((x1, y1, x2, y2, label))
                            youwu = True

                        # 只有一小部分的直接过滤//暂时舍弃
                        # elif int(xmin) < c or int(xmax) > c+h or int(ymin) < r or int(ymax) > r+w_win_size:
                        #     pass

                    if xiefou:
                        if youwu:
                            if mode=='VOC':
                                img_new_name = img_name + '_%05d.%s' % (i,img_mat)
                                lal_new_name = img_name + '_%05d.%s' % (i,label_mat)
                                img_save_path_1 = os.path.join(imgs_save_dir,img_new_name)
                                lal_save_path_1 = os.path.join(labels_save_dir, lal_new_name)
                                self.write_xml(tmp_PIL, temp_boxes, img_new_name, lal_save_path_1, img_save_path_1)
                    else:
                        print(f'{img_name}.{img_mat}切分至第{i}份框坐标x1,x2重合成线，忽略当前第{i}份图像！！！！！')

        def SplitAndTransform(self,mold='VOC'):
            JsonPaths, ImgPaths, PType = self.chackPath()
            if not JsonPaths or not ImgPaths:
                return
            mold = mold
            if mold == "VOC":
                Save_dir = JsonPaths.replace('labels', 'SplitVOCMoldData')
                save_img_dir = os.path.join(Save_dir, "JPEGImages")
                save_Ann_dir = os.path.join(Save_dir, "Annotations")
                save_img_dir_back = os.path.join(Save_dir, "JPEGImagesBackground")
                save_Ann_dir_back = os.path.join(Save_dir, "AnnotationsBackground")
                label_mat = 'xml'
            elif mold == "YOLO":
                Save_dir = JsonPaths.replace('labels', 'SplitYOLOMoldData')
                save_img_dir = os.path.join(Save_dir, "Images")
                save_Ann_dir = os.path.join(Save_dir, "Labels")
                save_img_dir_back = os.path.join(Save_dir, "ImagesBackground")
                save_Ann_dir_back = os.path.join(Save_dir, "LabelsBackground")
                label_mat = 'txt'

            self.check_file(save_img_dir)
            self.check_file(save_Ann_dir)
            self.del_dir(save_img_dir_back)
            self.del_dir(save_Ann_dir_back)


            if "板" in PType:
                EngCls = self.class_info_dict['板材']['英文']
            elif "棒" in PType:
                EngCls = self.class_info_dict['棒材']['英文']
            elif "铸" in PType:
                EngCls = self.class_info_dict['铸坯']['英文']
            elif "冷" in PType:
                EngCls = self.class_info_dict['冷轧']['英文']
            elif "热" in PType:
                EngCls = self.class_info_dict['热轧']['英文']
            elif "符" in PType:
                EngCls = self.class_info_dict['字符']['英文']
            else:
                QtWidgets.QMessageBox.warning(self, '错误', "请选择支持的产品类型样本集！！", )
                return
            info = {}
            info["classnames"] = EngCls
            with open(os.path.join(Save_dir, 'classnames.json'), 'w', encoding='utf8') as f:
                json.dump(info, f, indent=4, separators=(',', ': '))
            total_num = len(os.listdir(JsonPaths))
            for JsonPath in glob.glob(JsonPaths + "/*.json"):
                bk = 0
                ImagePath = JsonPath.replace('json', 'bmp').replace('labels', 'images')
                # print(ImagePath)
                if not os.path.exists(ImagePath):
                    ImagePath = JsonPath.replace('json', 'jpg').replace('labels', 'images')
                if not os.path.exists(ImagePath):
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    QtWidgets.QMessageBox.information(self, '提示', f"图片:{ImgName}.??? 不存在或者格式为非bmp、jpg! 点击OK键继续！", )
                    bk += 1
                if bk == 1:
                    self.Num += 1
                    self.pbar.setValue(self.Num / total_num * 100)
                    QtWidgets.QApplication.processEvents()
                    continue
                if platform.system() == "Windows":
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    ImgMat = ImagePath.split('\\')[-1].split('.')[1]
                elif platform.system() == "Linux":
                    ImgName = ImagePath.split('/')[-1].split('.')[0]
                    ImgMat = ImagePath.split('/')[-1].split('.')[1]

                self.clip_img(
                     ImagePath, ImgName, ImgMat,
                     JsonPath, label_mat,
                     EngCls, mold,
                     save_img_dir, save_Ann_dir,
                     save_img_dir_back,save_Ann_dir_back,
                     )

                self.Num += 1
                self.pbar.setValue(self.Num / total_num * 100)
                QtWidgets.QApplication.processEvents()

        def split_img_xml(self):
            self.SplitAndTransform(mold='VOC')

        def GetBBox(self,mold='VOC'):
            JsonPaths, ImgPaths, PType = self.chackPath()
            if not JsonPaths or not ImgPaths:
                return
            mold = mold
            if mold =="VOC":
                Save_dir = JsonPaths.replace('labels', 'VOCMoldData')
                save_img_dir = os.path.join(Save_dir, "JPEGImages")
                save_Ann_dir = os.path.join(Save_dir, "Annotations")
                save_img_dir_back = os.path.join(Save_dir, "JPEGImagesBackground")
                save_Ann_dir_back = os.path.join(Save_dir, "AnnotationsBackground")
                label_mat = 'xml'
            elif mold == "YOLO":
                Save_dir = JsonPaths.replace('labels', 'YOLOMoldData')
                save_img_dir = os.path.join(Save_dir, "Images")
                save_Ann_dir = os.path.join(Save_dir, "Labels")
                save_img_dir_back = os.path.join(Save_dir, "ImagesBackground")
                save_Ann_dir_back = os.path.join(Save_dir, "LabelsBackground")
                label_mat = 'txt'

            self.check_file(save_img_dir)
            self.check_file(save_Ann_dir)
            self.del_dir(save_img_dir_back)
            self.del_dir(save_Ann_dir_back)

            if "板" in PType:
                EngCls = self.class_info_dict['板材']['英文']
            elif "棒" in PType:
                EngCls = self.class_info_dict['棒材']['英文']
            elif "铸" in PType:
                EngCls = self.class_info_dict['铸坯']['英文']
            elif "冷" in PType:
                EngCls = self.class_info_dict['冷轧']['英文']
            elif "热" in PType:
                EngCls = self.class_info_dict['热轧']['英文']
            elif "符" in PType:
                EngCls = self.class_info_dict['字符']['英文']
            else:
                QtWidgets.QMessageBox.warning(self, '错误', "请选择支持的产品类型样本集！！", )
                return
            info ={}
            info["classnames"] = EngCls
            with open(os.path.join(Save_dir,'classnames.json'),'w',encoding='utf8') as f:
                json.dump(info,f,indent=4,separators=(',', ': '))

            total_num = len(os.listdir(JsonPaths))
            image_index = 0
            for JsonPath in glob.glob(JsonPaths + "/*.json"):
                bk = 0
                ImagePath = JsonPath.replace('json', 'bmp').replace('labels', 'images')
                # print(ImagePath)
                if not os.path.exists(ImagePath):
                    ImagePath = JsonPath.replace('json', 'jpg').replace('labels', 'images')
                if not os.path.exists(ImagePath):
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    QtWidgets.QMessageBox.information(self, '提示', f"图片:{ImgName}.??? 不存在或者格式为非bmp、jpg! 点击OK键继续！", )
                    bk += 1
                if bk == 1:
                    image_index += 1
                    self.pbar.setValue(image_index / total_num * 100)
                    QtWidgets.QApplication.processEvents()
                    continue
                if platform.system() == "Windows":
                    ImgName = ImagePath.split('\\')[-1].split('.')[0]
                    ImgMat = ImagePath.split('\\')[-1].split('.')[1]
                elif platform.system() == "Linux":
                    ImgName = ImagePath.split('/')[-1].split('.')[0]
                    ImgMat = ImagePath.split('/')[-1].split('.')[1]

                #映射新路径
                img_save_path_1 = os.path.join(save_img_dir,ImgName+f".{ImgMat}")
                lal_save_path_1 = os.path.join(save_Ann_dir,ImgName+f".{label_mat}")

                ImagePIL = Image.open(ImagePath).convert('L')  # w,h
                img_name = ImgName+f".{ImgMat}"
                data = json.load(open(JsonPath, 'r', encoding='utf8'))
                shapeList = data['shapes']
                box_info = []
                for shape in shapeList:
                    if shape['shape_type'] == 'rectangle':
                        points = shape['points']
                        x1,y1,x2,y2 = points[0][0],points[0][1],points[1][0],points[1][1]
                        x1_tmp = min(x1,x2)
                        y1_tmp = min(y1,y2)
                        x2_tmp = max(x1,x2)
                        y2_tmp = max(y1,y2)
                        x1, y1, x2, y2 = x1_tmp, y1_tmp, x2_tmp, y2_tmp
                        className = shape["label"]
                        if str(className) not in EngCls:
                            QtWidgets.QMessageBox.information(self, '提示', f"类别{className}:不属于当前{PType}类型类别! 点击OK继续！！！")
                            continue
                        box_info.append([x1, y1, x2, y2, className])

                if len(box_info) == 0:
                    if not os.path.exists(save_img_dir_back):
                        os.makedirs(save_img_dir_back)
                    if not os.path.exists(save_Ann_dir_back):
                        os.makedirs(save_Ann_dir_back)

                    img_save_path_2 = os.path.join(save_img_dir_back, ImgName + f".{ImgMat}")
                    lal_save_path_2 = os.path.join(save_Ann_dir_back, ImgName + f".{label_mat}")
                    ImagePIL.save(img_save_path_2)
                    lbl_file = open(lal_save_path_2,'wb+',encoding='utf8')
                    lbl_file.close()
                    image_index += 1
                else:
                    if mold == 'VOC':
                        self.write_xml(ImagePIL,box_info,img_name,lal_save_path_1,img_save_path_1)
                    elif mold == 'YOLO':
                        self.write_txt(ImagePIL,box_info,lal_save_path_1,img_save_path_1,EngCls)
                    image_index += 1

                self.pbar.setValue(image_index / total_num * 100)
                QtWidgets.QApplication.processEvents()
                # time.sleep(0.05)

        def write_txt(self,img,boxes,txt_path,img_path,class_name):
            #坐标转换
            def convert(size, box):
                dw = 1. / size[0]
                dh = 1. / size[1]
                x = (box[0] + box[1]) / 2.0
                y = (box[2] + box[3]) / 2.0
                w = box[1] - box[0]
                h = box[3] - box[2]
                x = x * dw
                w = w * dw
                y = y * dh
                h = h * dh
                return (x, y, w, h)

            label_file = open(txt_path, 'w', encoding='utf-8')
            sizee=img.size
            for box in boxes:
                cls = box[-1]
                cls_id = class_name.index(cls)
                bbox = [box[0],box[2],box[1],box[3]]
                bb = convert(sizee,bbox)
                label_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')
            label_file.close()
            img.save(img_path)

        def write_xml(self,img,boxes,img_name,xml_path,img_path):
            # 创建xml函数
            def create_xml_node(node_name, node_txt, node_object):
                op = doc.createElement(str(node_name))
                txt = doc.createTextNode(str(node_txt))
                op.appendChild(txt)
                node_object.appendChild(op)

            def create_obj_node(box_label, xmin, ymin, xmax, ymax):
                # 创建annotation下的子节点 object
                object_info = doc.createElement('object')
                annotation.appendChild(object_info)
                # 创建annotation下的子节点name  并写入文本内容
                create_xml_node('name', box_label, object_info)
                # 创建annotation下的子节点difficult  并写入文本内容
                create_xml_node('difficult', '0', object_info)
                # 创建annotation下的子节点bndbox
                bndbox = doc.createElement('bndbox')
                object_info.appendChild(bndbox)
                # 创建bndbox下的子节点xmin，创建xmin真实值的节点，将节点添加到父节点
                create_xml_node('xmin', xmin, bndbox)
                # ymin节点
                create_xml_node('ymin', ymin, bndbox)
                # xmax节点
                create_xml_node('xmax', xmax, bndbox)
                # ymax节点
                create_xml_node('ymax', ymax, bndbox)

            use_img_w, use_img_h = img.size
            if img.mode is 'RGB':
                use_img_depth = 3
            else:
                use_img_depth = 1


            # write xml info
            doc = Document()
            annotation = doc.createElement('annotation')
            doc.appendChild(annotation)
            # filename
            create_xml_node('filename', img_name, annotation)
            # size
            object_size = doc.createElement('size')
            annotation.appendChild(object_size)
            # width
            create_xml_node('width', use_img_w, object_size)
            # height
            create_xml_node('height', use_img_h, object_size)
            # depth
            create_xml_node('depth', use_img_depth, object_size)

            for ii in range(len(boxes)):
                imgback_box = boxes[ii]
                if imgback_box:
                    xmin, ymin, xmax, ymax, label = imgback_box
                    # write box info
                    create_obj_node(label, int(xmin), int(ymin), int(xmax), int(ymax))

            with open(xml_path, 'wb+') as f:
                f.write(doc.toprettyxml(indent="\t", encoding='utf-8'))  # encoding='utf-8'
            img.save(img_path)

        def renameFiles(self,dirPath,Mat,Ttime,Tname,Count):
            CountNow =Count
            num = 0
            total_num = len(os.listdir(dirPath))
            for FileName in os.listdir(dirPath):
                if FileName.split(".")[-1] ==Mat:
                    CountCr = "%06d"%CountNow
                    FileNameNew = FileName.replace(FileName.split(".")[0],str(Tname)+"_"+str(Ttime)+"_"+CountCr)
                    FilePathNew = os.path.join(dirPath,FileNameNew)
                    filePathOld = os.path.join(dirPath,FileName)
                    os.rename(filePathOld,FilePathNew)
                    CountNow +=1
                num +=1
                self.pbar.setValue(num/total_num *100)
                QtWidgets.QApplication.processEvents()
                # time.sleep(0.05)

        def GetInfo(self):
            path_req = self.get_directory_path
            # print(str(self.dateEdit1.dateTime().toPyDateTime()))
            # print(help(self.dateEdit1.dateTime()))
            try:
                time_info = str(self.dateEdit1.dateTime().toPyDateTime())[:-7]
            except:
                time_info = str(self.dateEdit1.dateTime().toPython())[:-7]
            n_time11 = time.strptime(time_info, "%Y-%m-%d %H:%M:%S")
            n_time1 = int(time.strftime('%Y%m%d%H%M%S', n_time11))
            text_name = self.lin_2.text()

            if not path_req :
                QtWidgets.QMessageBox.warning(self, '错误',"请选择非空目录！！")
            else:
                if glob.glob(path_req+"/*bmp") or glob.glob(path_req+"/*jpg"):
                    if text_name and not self.isInZh(str(text_name)):
                        if glob.glob(path_req + "/*bmp"):
                            self.renameFiles(path_req, "bmp", n_time1, text_name, 0)
                        if glob.glob(path_req + "/*jpg"):
                            self.renameFiles(path_req, "jpg", n_time1, text_name, 0)

                        reply = QtWidgets.QMessageBox.question(self, '提示',
                                                     "重命名完成，是否进行页面跳转", QtWidgets.QMessageBox.Yes |
                                                     QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                        if reply == QtWidgets.QMessageBox.Yes:
                            self.switchWin()
                    elif self.isInZh(str(text_name)):
                        QtWidgets.QMessageBox.warning(self, '错误',"请按照格式输入！！",)
                    else:
                        QtWidgets.QMessageBox.warning(self, '错误',"请在标注者中输入身份！",)
                else:
                    QtWidgets.QMessageBox.warning(self, '错误', "请选择更改名称的图片所在目录！！", )

        def initUI(self):
            #进度条
            self.Num = 0
            #创建一个进度条
            self.pbar = QtWidgets.QProgressBar(self)
            self.pbar.setMinimum(0)  # 设置进度条最小值
            self.pbar.setMaximum(100)  # 设置进度条最大值
            self.pbar.setValue(0)  # 进度条初始值为0
            self.pbar.setGeometry(350, 300, 250, 30)

            #创建一个菜单
            self.MenuBtn =QtWidgets.QPushButton("选项",self)
            #创建一个菜单对象
            self.Menu = QtWidgets.QMenu()
            #菜单中的选项
            ch_action = QtWidgets.QAction('修改文件名',self)  # 创建对象
            ch_action.triggered.connect(self.GetInfo)
            cls_action = QtWidgets.QAction('分类格式', self)  # 创建对象
            cls_action.triggered.connect(self.GenClsData)
            det_action = QtWidgets.QAction('VOC格式', self)  # 创建对象
            det_action.triggered.connect(self.GenVOCDate)
            yl_action = QtWidgets.QAction('YOLO格式', self)  # 创建对象
            yl_action.triggered.connect(self.GenYOLODate)
            seg_action = QtWidgets.QAction('分割格式', self)  # 创建对象
            seg_action.triggered.connect(self.GenSegData)
            seg_action = QtWidgets.QAction('切分模式', self)  # 创建对象
            seg_action.triggered.connect(self.split_img_xml)

            self.Menu.addActions([ch_action,cls_action,det_action,yl_action,seg_action])  # 将图标添加到菜单中
            self.MenuBtn.setMenu(self.Menu)  # 将菜单添加到按键中

            self.btsec = QtWidgets.QPushButton("选择文件夹", self)
            self.btsec.clicked.connect(self.openFile)
            """
            self.btok = QtWidgets.QPushButton("修改文件名", self)
            self.btok.clicked.connect(self.GetInfo)
            #获取训练数据
            self.btcls = QtWidgets.QPushButton("分类格式", self)
            # self.btok.clicked.connect(self.GetInfo)
            self.btdet = QtWidgets.QPushButton("检测格式", self)
            self.btyl = QtWidgets.QPushButton("YOLO格式", self)
            self.btmask = QtWidgets.QPushButton("分割格式", self)
            """

            self.btno = QtWidgets.QPushButton("跳转", self)
            self.btno.clicked.connect(self.switchWin)


            self.btsec.move(100,300)
            self.MenuBtn.move(250,300)
            '''
            self.btok.move(250, 200)
            self.btcls.move(250,1.5*self.btcls.height()+self.btok.y())
            self.btdet.move(250,1.5*self.btdet.height()+self.btcls.y())
            self.btyl.move(250,1.5*self.btyl.height()+self.btdet.y())
            self.btmask.move(250,1.5*self.btmask.height()+self.btyl.y())
            '''
            self.btno.move(self.btsec.x(), 310+self.btno.height())
            #
            self.label1 = QtWidgets.QLabel('标注时间:',self)
            self.curr_time = QtCore.QDateTime.currentDateTime()
            self.dateEdit1 = QtWidgets.QDateTimeEdit(self.curr_time, self)

            self.dateEdit1.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
            self.dateEdit1.resize(200,30)
            self.dateEdit1.move(self.width()//3,self.height()//6)
            self.label1.resize(100, 30)
            self.label1.move(self.dateEdit1.x()-0.7*self.label1.width(),self.dateEdit1.y())

            #
            self.label2 = QtWidgets.QLabel('标注者:', self)
            self.label2.move(self.label1.x(),self.dateEdit1.y()+self.dateEdit1.height()*2)
            self.lin_2 = QtWidgets.QLineEdit(self)
            self.lin_2.setPlaceholderText('请使用英文或者拼音！！')
            self.lin_2.resize(200,30)
            self.lin_2.move(self.label2.x()+0.7*self.label2.width(),self.label2.y())
            self.setGeometry(300, 300, 600, 500)
            self.setWindowTitle('标注工具[测试版本v1.0.0]:BKVISION')

            #固定窗口大小
            self.setFixedSize(self.width(),self.height())
            self.show()

    one_win = First(win,class_names)
    one_win.show()
    sys.exit(app.exec_())


# this main block is required to generate executable by pyinstaller
if __name__ == "__main__":
    main()
