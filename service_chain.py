from enum import Enum, unique


@unique
class NetworkFunctionName(Enum):
    fun_1 = ['0', 0, 200]  # name, thread, throughput
    fun_2 = ['1', 1, 100]
    fun_3 = ['2', 0, 300]
    fun_4 = ['3', 1, 500]


# This is an instance of a VNF
class NetworkFunction(object):
    counter = 0

    def __init__(self, name):
        self.install_time = 1  # default installation time of a VNF is one TS
        self.name = name.value[0]
        # 0: single thread, 1: multi-thread
        self.thread_attr = name.value[1]
        self.throughput = name.value[2]
        self.index = NetworkFunction.counter
        NetworkFunction.counter += 1
        self.process_time = 0  # The time for processing time
        self.start_time = 0  # The start processing time
        self.idle_length = 60
        self.active_state = True

    def new_function(self):
        pass

    def set_start_time(self, start_time):
        self.start_time = start_time

    # def get_available_time(self):
        # return self.finish_time

    def set_processing_time(self, processing_time):
        self.process_time = processing_time

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



