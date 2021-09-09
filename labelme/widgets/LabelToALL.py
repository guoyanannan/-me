import os
import json
import numpy as np
from PIL import  Image

path  =  r"C:\Users\guoyaya\Desktop\安钢现场"

print(os.listdir(path))

if not ("images" and "labels1") in os.listdir(path):
    print(1111111111111)