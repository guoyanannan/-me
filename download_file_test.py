from urllib import request
import math
import os
# PATH_BIN = f'C:/Users/{os.getlogin()}/classname.bin'
PATH_BIN = f'C:/ProgramData/Annotationtool/classname.bin'
url = 'https://gitee.com/worldofyanan/annotation_tool/raw/master/classname.bin'
print ("downloading with urllib.............")
# download= url.split('/')[-1]#这里是直接按照原来的文件名下载，如果有需要可以自己修改
# request.urlretrieve(url, download)
try:
    if not os.path.exists(os.path.dirname(PATH_BIN)):
        os.makedirs(os.path.dirname(PATH_BIN))
    _ = request.urlretrieve(url, PATH_BIN)
    print(math.ceil(os.path.getsize(PATH_BIN)/1024),'kb')
except Exception as E:
    print(E)


# import os
# print(__file__)
# print(os.getcwd())
# print(os.path.split(__file__))
# print(os.path.basename(__file__))
# print(os.path.dirname(__file__))
# print(os.path.abspath(__file__))
