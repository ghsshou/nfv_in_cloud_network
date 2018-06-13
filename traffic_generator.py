import math
import random
import request_type
import numpy as np
import network_info as ni
import math


class TrafficGenerator(object):
    counter = 0

    def __init__(self, input_lambda, input_mu, max_req_num, optional_data_size=[]):
        self._lambda = input_lambda
        self._mu = input_mu
        self._max_req_num = max_req_num
        self.optional_data_size = optional_data_size
        self.time_slot_length = ni.global_TS  # Length of a time slot in ms
        self.control_factor = 0.1  # To control the arriving time
        # The deadline for a request is basic_deadline + deadline_length * random()
        self.basic_deadline = 40
        self.deadline_length = 40
        self.ddl_scale = 1.2  # The scale factor for deadline according to the processing time
        # The optional data size of a request
        self.basic_size = 10
        self.size_length = 9.5
        # Sleep time
        self.sleep_time =[]
        self.req_set = []

    def generate_one_req(self, sc_size, user_node, data_size_flag="continuous"):
        req_sc = int(random.random() * sc_size)
        user_list = list(user_node)
        src_index = int(random.random() * len(user_list))
        dst_index = int(random.random() * len(user_list))
        # Ensure the source node should not be the same as the destination node
        while src_index == dst_index:
            dst_index = int(random.random() * len(user_list))
        if data_size_flag != "continuous":
            data_size_index = int(random.random() * len(self.optional_data_size))
            req_data_size = self.optional_data_size[data_size_index]
        else:
            req_data_size = self.basic_size + self.size_length * random.random()
        req_deadline = self.basic_deadline + int(self.deadline_length * random.random())
        new_request = request_type.Request(user_list[src_index], user_list[dst_index], req_sc, req_data_size,
                                           req_deadline)
        return new_request

    def generate_traffic(self, sc_size, user_node, data_size_flag="continuous"):
        (self.sleep_time, arr_time, average_duetime) = self.poisson_traffic(self._lambda, self._max_req_num)
        print("Average Arrive Interval:", average_duetime)
        for i in range(self._max_req_num):
            self.req_set.append(self.generate_one_req(sc_size, user_node, data_size_flag))
            self.req_set[i].arr_time = arr_time[i]

    # Modify the deadline for each request, return the average deadline of all requests
    def deadline_revise(self, data_base):
        ave = 0
        for req in self.req_set:
            req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the name of vnfs
            est_time = 0
            for vnf_type in req_vnfs:
                est_time += req.data_size / vnf_type.value[2] / ni.global_TS
            req.deadline = math.ceil(est_time * self.ddl_scale)  # the scale factor
            ave += est_time
        return ave / len(self.req_set)

    def customize_request(self, src_node, dst_node,  sc_req, data_size, arr_time, ddl):
        new_request = request_type.Request(src_node, dst_node, sc_req, data_size, ddl)
        new_request.arr_time = arr_time
        return new_request

    def print_all_requests(self):
        for req in self.req_set:
            print(req)

    def print_sleep_time(self):
        result = []
        for value in self.sleep_time:
            result.append(value)
            print(value)
        return result

    def poisson_traffic(self, lam, max_num):
        traffic = np.random.poisson(lam, max_num)
        traffic = [x * self.time_slot_length * self.control_factor for x in traffic]
        ave_duetime = np.mean(traffic)
        result = []
        val = 0
        for index in traffic:
            val += index
            result.append(val)
        return traffic, result, ave_duetime
