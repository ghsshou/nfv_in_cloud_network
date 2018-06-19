import service_chain
import traffic_generator
import network_info
import matplotlib.pyplot as pl
import data_base
import request_process
import time

if __name__ == "__main__":
    # Get a database
    data_base = data_base.DataBase()
    # Initialize the network function information
    function_set = []
    # vnf1 = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_1)
    # data_base.add_vnf(vnf1)
    # vnf2 = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_2)
    # function_set.append(vnf2)
    # vnf3 = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_3)
    # function_set.append(vnf3)
    # Service chain information
    # new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2)
    # data_base.scs.add_sc(new_sc)
    new_sc = [service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2
              ]
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_3, service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_2, service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2,
              service_chain.NetworkFunctionName.fun_3, service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_3,
              service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    # data_base.scs.print_all_scs()
    # Network initialize
    data_center = ["0", "10", "4"]
    data_base.add_datacenter(data_center)
    # Traffic generator initialize
    # Para: lambda, mu, request number, optional data size
    traffic_num = 1000
    data_base.set_traffic_generator(5, 0.001, traffic_num, [4, 6, 8, 10])
    # data_base.tf_gen.print_all_requests()
    # l = data_base.tf_gen.print_sleep_time()
    # x = list(range(1000))
    # pl.hist(l, 10, color='red')
    # pl.scatter(x, l)
    # pl.show()
    # test add vm and vmf
    # data_base.start_new_vm(1, 1, '0')
    # data_base.install_vnf_to_vm(vnf1, data_base.vms[0])
    # req1 = data_base.tf_gen.customize_request("13", "8", 0, 4.12, 3, 763)
    # req2 = data_base.tf_gen.customize_request("1", "10", 1, 5, 16, 78)
    # request_process.algorithm_x(data_base, req1)
    # request_process.algorithm_x(data_base, req2)
    # request_process.process_one_req(data_base, data_base.tf_gen.req_set[0])
    # request_process.process_one_req(data_base, data_base.tf_gen.req_set[1])
    # request_process.process_one_req(data_base, req1)
    # request_process.process_one_req(data_base, req2)
    for i in range(traffic_num):
        # request_process.process_one_req(data_base, data_base.tf_gen.req_set[i])
        request_process.algorithm_x(data_base, data_base.tf_gen.req_set[i])
        time.sleep(data_base.tf_gen.sleep_time[i] * network_info.global_TS * data_base.tf_gen.control_factor)

    # time.sleep(3)
    data_base.get_cost()
    data_base.get_used_vm_no()
    data_base.print_req_provisioning()
    print("Average Latency: " + str(round(data_base.average_latency(), 3)) + "s")
    print("BP: " + str(data_base.blocking_probability() * 100) + "%")
    # data_base.print_all_vms()






