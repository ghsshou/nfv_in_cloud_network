from enum import Enum, unique


@unique
class NetworkFunctionName(Enum):
    fun_1 = ['0', 0, 2]  # name, thread, throughput
    fun_2 = ['1', 1, 1]
    fun_3 = ['2', 0, 3]
    fun_4 = ['3', 2, 5]


# This is an instance of a VNF
class NetworkFunction(object):
    counter = 0

    def __init__(self, name):
        self.name = name.value[0]
        # 0: single thread, 1: multi-thread
        self.thread_attr = name.value[1]
        self.throughput = name.value[2]
        self.index = NetworkFunction.counter
        NetworkFunction.counter += 1
        self.finish_time = 0
        self.idle_length = 0
        self.active_state = True

    def new_function(self):
        pass

    def get_available_time(self):
        return self.finish_time

    def set_finish_time(self, fin_time):
        self.finish_time = fin_time

    def __str__(self):
        return "VNF " + self.name


class ServiceChains(object):
    # The index denotes different kind of service chains
    def __init__(self):
        self.sc_set = []

    def add_sc(self, sc):
        self.sc_set.append(sc)

    def get_size(self):
        return len(self.sc_set)

    # Get one service chain
    def get_sc(self, index):
        return self.sc_set[index]

    def print_all_scs(self):
        i = 0
        for sc in self.sc_set:
            print("SC" + str(i) + ": ", end="")
            for fun in sc:
                print(fun, " ", end="")
            print()



