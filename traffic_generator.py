import math
import random
import request_type
import numpy as np
import network_info as ni
import math
import logging


class TrafficGenerator(object):
    # counter = 0

    def __init__(self, input_lambda, ddl_scale, max_req_num, optional_data_size=[]):
        self.ddl_type_list = ('fixed', 'variable', 'unlimited')
        self._lambda = input_lambda
        # self._mu = input_mu
        self._max_req_num = max_req_num
        self.optional_data_size = optional_data_size
        self.time_slot_length = ni.global_TS  # Length of a time slot in s
        self.control_factor = 0.05  # To control the arriving time
        # The deadline for a request is basic_deadline + deadline_length * random()
        self.basic_deadline = 40
        self.deadline_length = 40
        self.ddl_scale = ddl_scale  # The scale factor for deadline according to the processing time
        # The optional data size of a request
        self.basic_size = 1
        self.size_length = 4
        # Sleep time
        self.sleep_time = []
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
        req_ddl_type = self.ddl_type_list[int(len(self.ddl_type_list) * random.random())]
        req_deadline = self.basic_deadline + int(self.deadline_length * random.random())
        new_request = request_type.Request(user_list[src_index], user_list[dst_index], req_sc, req_data_size,
                                           req_deadline, req_ddl_type)
        # print("REQ: ", new_request.counter, " ddl_type:", new_request.ddl_type)
        return new_request

    def generate_traffic(self, sc_size, user_node, data_size_flag="continuous"):
        (self.sleep_time, arr_time, average_interval_time) = self.poisson_traffic(self._lambda, self._max_req_num)
        logging.info("Average Arrive Interval:" + str(average_interval_time * ni.global_TS))
        for i in range(self._max_req_num):
            self.req_set.append(self.generate_one_req(sc_size, user_node, data_size_flag))
            self.req_set[i].arr_time = arr_time[i]
        return average_interval_time * ni.global_TS

    # Modify the deadline for each request, return the average deadline of all requests
    def deadline_revise(self, data_base):
        ave = 0
        for req in self.req_set:
            req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the name of vnfs
            est_time = 0
            for vnf_type in req_vnfs:
                est_time += math.ceil(req.data_size / vnf_type.value[2] / ni.global_TS)
                est_time += 2 * math.ceil(req.data_size / ni.trans_cap / ni.global_TS)
            if req.ddl_type == self.ddl_type_list[0]:  # fixed ddl
                req.deadline = math.ceil(est_time * self.ddl_scale)  # the scale factor
                # if req.deadline < 100:
                #     req.deadline = req.deadline * 1.7
            if req.ddl_type == self.ddl_type_list[1]:  # variable ddl
                req.deadline = (math.ceil(est_time * self.ddl_scale), math.ceil(est_time * self.ddl_scale * 4))
                ave += req.deadline[0]
            if req.ddl_type == self.ddl_type_list[2]:  # unlimited
                req.deadline = math.inf
        return ave / len(self.req_set)

    @staticmethod
    def customize_request(src_node, dst_node, sc_req, data_size, arr_time, ddl):
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
        lam_in_TS = lam / self.time_slot_length
        traffic = np.random.poisson(lam_in_TS, max_num)
        # traffic = [x / self.time_slot_length for x in traffic]
        ave_duetime = np.mean(traffic)
        result = []
        val = 0
        for index in traffic:
            val += index
            result.append(val)
        return traffic, result, ave_duetime
