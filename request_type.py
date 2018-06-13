class Request(object):
    counter = 0

    def __init__(self, src, dst, sc, data_size, deadline, arr_time=0):
        self.src = src
        self.dst = dst
        self.sc = sc
        self.data_size = data_size
        self.arr_time = arr_time
        self.deadline = deadline
        self.counter = Request.counter
        Request.counter = Request.counter + 1

    def __str__(self):
        return "[REQ " + str(self.counter) + ":" + self.src + "->" + self.dst + ", SC type: " + str(self.sc) + \
            ", Data size: " + str(self.data_size) + ", Arrives at: " + str(self.arr_time)\
               + ", Deadline: " + str(self.deadline) +"]"


if __name__ == "__main__":
    print(str(Request("0", "0", 0, 0, 0, 0)))
    print(Request("1", "1", 1, 1, 1, 1))
