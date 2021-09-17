import imgviz,os
import numpy as np
from PIL import Image



path = r'C:\Users\guoyaya\Desktop\板材\安钢项目\SegmentationData\SegLabels'

file_names = os.listdir(path)
for file_name in file_names:
    file_path = os.path.join(path,file_name)
    Img_data = Image.open(file_path)
    Img_arr = np.array(Img_data)
    print(np.unique(Img_arr.ravel()[np.flatnonzero(Img_arr)]))
    Img_arr_rgb = imgviz.label2rgb(Img_arr)
    print(np.unique(Img_arr_rgb.ravel()[np.flatnonzero(Img_arr_rgb)]))
    Img_arr_rgb_pl = Image.fromarray(Img_arr_rgb)
    Img_arr_rgb_pl.show()