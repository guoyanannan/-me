from urllib import request
import shutil
import os

url = 'https://raw.githubusercontent.com/guoyanannan/-me/master/bankdata.bin'
print ("downloading with urllib")
download= url.split('/')[-1]#这里是直接按照原来的文件名下载，如果有需要可以自己修改
# request.urlretrieve(url, download)
try:
    _ = request.urlretrieve(url, download)
    print(os.path.getsize(download)//1024)
except Exception as E:
    print(E)


# import os
# print(__file__)
# print(os.getcwd())
# print(os.path.split(__file__))
# print(os.path.basename(__file__))
# print(os.path.dirname(__file__))
# print(os.path.abspath(__file__))
