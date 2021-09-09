import os
# a = "你好"
# b = "</p>你好"
# c = 'asdf'
#
#
# def isAllZh(s):
#     for c in s:
#         if '\u4e00' <= c <= '\u9fa5':
#             return True
#     return False
#
#
# print(isAllZh(a))
# print(isAllZh(b))
# print(isAllZh(c))
# import glob
#
# a = glob.glob("./测试下拉框/*bmp")
# if a:
#     print(11111)
# print(a)
# dirPath = r"C:\Users\guoyaya\Desktop\485754 - 副本 (2)"
# Tname = "ls"
# Ttime = "20111020"
# count = 0
# for FileName in os.listdir(dirPath):
#     if FileName.split(".")[-1] == "bmp":
#         count_cv = "%06d"%count
#         FileNameNew = FileName.replace(FileName.split(".")[0], str(Tname) + "_" + str(Ttime)+ "_" +count_cv)
#         FilePathNew = os.path.join(dirPath, FileNameNew)
#         filePathOld = os.path.join(dirPath, FileName)
#         os.rename(filePathOld, FilePathNew)
#         count +=1

#
# a =10
# def p():
#     global a
#     a += 10
#     b = a+10
#
#     print(b,a)
#
# print(a)
#
# p()
# print(a)