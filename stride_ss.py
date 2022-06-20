
win = 2048
stride = win-1
while True:
    win_step = 8*1024 -win
    if win_step%stride==0:
        print(stride)
        break
    else:
        stride -=1