from threading import Thread
import time
import numpy as np
n = np.ones((3,3))
# n = 100
print(n,id(n))



def func1(num):
    print(id(num))
    num = num.copy()
    num += 10
    print('num1:',num,id(num))

def func2(num):
    print(id(num))
    time.sleep(2)
    print('num2:',num,id(num))

th1 = Thread(target=lambda :func1(n))
th2 = Thread(target=lambda :func2(n))
th1.start()
th2.start()

