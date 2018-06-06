# import numpy as np
# import matplotlib.pyplot as plt
#
# s = np.random.poisson(5, 10000)
# count, bins, ignored = plt.hist(s, 14, normed=True)
# plt.show()

# import threading
# import random
# import numpy as np
#
#
# def fun_random_set(list_tt):
#     index = np.random.randint(len(list_tt))
#     if list_tt[index] == 1:
#         list_tt[index] = 0
#     else:
#         list_tt[index] = 1
#     print(list_tt)
#
#
# list_tt = np.random.randint(0, 2, 10).tolist()
# for i in range(10):
#     timer = threading.Timer(5.0, fun_random_set, args=(list_tt,))
#     timer.start()
import numpy as np
import threading, time


# list_t = np.random.randint(1, 2, 10).tolist()
# print(list_t)
# counter = 0
#
#
# def every_change(list_t, counter):
#     print("Thread name:", threading.current_thread().name)
#     list_t[counter] = 0
#     print("Have changed to:", list_t)
#     time.sleep(2)
#     list_t[counter] = 1
#     print("Changed back to", list_t)
#
# i = 0
# while(i < len(list_t)):
#     t = threading.Thread(target=every_change, args=(list_t, counter))
#     t.start()
#     t.join()
#     i += 1
#     counter += 1
# import threading, time
# def print_a_word(i):
#     print("Hello:", str(i))
#     time.sleep(3)
#     print(threading.current_thread().name + "Finish")
#
# i = 0
# thread_list = []
# while i < 10:
#     print("Now process:" + str(i))
#     t = threading.Thread(target=print_a_word, args=(i,))
#     thread_list.append(t)
#     i += 1
# for t in thread_list:
#     t.start()
# for t in thread_list:
#     t.join()

from enum import Enum, unique
class CPUPrice(Enum):
    z1 = ['0', 0.00698]  # name, price (per CPU per hour)
    z2 = ['1', 0.00798]
    z3 = ['2', 0.00598]

for xx in CPUPrice:
    print(xx.value[0])






