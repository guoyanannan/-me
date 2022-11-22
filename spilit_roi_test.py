import math
import cv2
import numpy as np
from PIL import Image

i = 0
w_win_size = 1024
h_win_size = 1024
stride = 1024-256
# h 900 1600 1024 2048 2200
# img_path = './img/yingji_ckg_20220614084753_000048.bmp'
# img_path = './img/yingji_ckg_20220614084753_000049.bmp'
# img_path = './img/yingji_ckg_20220614084753_000050.bmp'
# img_path = './img/yingji_ckg_20220614084753_000074.bmp'
# img_path = './img/yingji_ckg_20220614084753_000077.bmp'
# img_path = './img/yingji_ckg_20220614084753_000078.bmp'
img_path = './img/yingji_ckg_20220614084753_000079.bmp'
img_pil = Image.open(img_path).convert('L')
w,h = img_pil.size
print(w,h)
img = np.array(img_pil,np.uint8)
img_rgb = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
debug = True
# if resolution.lower() == '4k'.lower():
#     stride = 1024 - 256  # 重叠的大小（768），设置这个可以使分块有重叠  stride =win_size 说明设置的分块没有重叠
# else:
#     stride = 896
# print('h_-1:',h % stride)
# if h <= 1280:
#     h_step_num = 1
# elif h % stride <= 512:
#     h_step_num = h // stride
# else:
#     h_step_num = h // stride+1
# print('w_-1:',w % stride)
# if w <= 1280:
#     w_step_num = 1
# elif w % stride <= 512:
#     w_step_num = w//stride
# else:
#     w_step_num = w // stride + 1
is_h_break = False
is_w_break = False
for j in range(0, h, stride): # r
    for k in range(0, w, stride): # c
        print(f'r:{j} c:{k}')
    #for c in range(0, (w - w_win_size) + 1, stride):  # W方向进行切分
        # flag = np.zeros([1, len(res)])  # 修改flag = np.zeros([1, len(res)])
        youwu = False  # 是否有物体
        xiefou = True  # 是否记录
        is_w_break = False
        is_h_break = False
        y1_,y2_,x1_,x2_ = j,j+h_win_size,k,k+w_win_size
        print('前',x1_,y1_,x2_,y2_)
        if h - y2_ <= 256:
            y2_ = h
            if y2_-y1_ < h_win_size:
                y1_ = y2_ - h_win_size
                if y1_ <0:
                    y1_ = 0
            is_h_break = True
        else:
            pass
            # if y2_ >= h:
            #     out_pixel_h = y2_ - h
            #     y1_ = y1_ - out_pixel_h
            #     y2_ = y2_ - out_pixel_h
            #     if y1_ <0:
            #         y1_ = 0
            #     is_h_break = True
        if w-x2_ <= 256:
            x2_ = w
            if x2_ - x1_ < w_win_size:
                x1_ = x2_ - w_win_size
                if x1_ < 0:
                    x1_ = 0
            is_w_break = True
        else:
            pass
            # if x2_ >= w:
            #     out_pixel_w = x2_ - w
            #     x1_ = x1_ - out_pixel_w
            #     x2_ = x2_ - out_pixel_w
            #     if x1_ <0:
            #         x1_ = 0
            #     is_w_break = True

        # if y2_ >= h:
        #     out_pixel_h = y2_-h
        #     y1_ = y1_ - out_pixel_h
        #     y2_ = y2_ - out_pixel_h
        #
        # if x2_ >= w:
        #     out_pixel_w = x2_-w
        #     x1_ = x1_ - out_pixel_w
        #     x2_ = x2_ - out_pixel_w

        # tmp = img[r: r + h_win_size, c: c + w_win_size]
        print('后:',x1_,y1_,x2_,y2_)
        tmp = img[y1_: y2_, x1_: x2_]
        print(tmp.shape)
        # r, c = y2_, x2_
        # c = x2_
        tmp_PIL = Image.fromarray(tmp)
        r = y1_
        c = x1_
        if debug:
            tmp_cr = np.random.randint(0, 255, 3, np.uint8)
            rgb_cr = (int(tmp_cr[0]), int(tmp_cr[1]), int(tmp_cr[2]))
            # print(rgb_cr)
            cv2.rectangle(img_rgb, (c, r), (x2_, y2_), rgb_cr, 12)
            cv2.namedWindow('haha', 0)
            cv2.imshow('haha', img_rgb)
            cv2.waitKey()
        i = i + 1
        if is_w_break:
            break
    if is_w_break and is_h_break:
        break