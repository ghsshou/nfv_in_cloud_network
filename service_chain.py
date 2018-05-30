from enum import Enum, unique


@unique
class NetworkFunctionName(Enum):
    fun_1 = '0'
    fun_2 = '1'
    fun_3 = '2'
    fun_4 = '3'


class NetworkFunction(object):
    def __init__(self, name, thread_attr, throughput):
        self.name = name
        # 0: single thread, 1: multi-thread
        self.thread_attr = thread_attr
        self.throughput = throughput

    def new_function(self):
        pass

    def __str__(self):
        return self.name


class ServiceChains(object):
    def __init__(self):
        self.sc_set = []

    def add_sc(self, sc):
        self.sc_set.append(sc)

    def get_size(self):
        return len(self.sc_set)

    def print_all_scs(self):
        i = 0
        for sc in self.sc_set:
            print("SC" + str(i) + ": ", end="")
            for fun in sc:
                print(fun, " ", end="")
            print()



