import service_chain
import traffic_generator
import network_info
import matplotlib.pyplot as pl
import data_base
import request_process

if __name__ == "__main__":
    # Get a database
    data_base = data_base.DataBase()
    # Initialize the network function information
    function_set = []
    vnf1 = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_1)
    # data_base.add_vnf(vnf1)
    # vnf2 = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_2)
    # function_set.append(vnf2)
    # vnf3 = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_3)
    # function_set.append(vnf3)
    # Service chain information
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2)
    data_base.scs.add_sc(new_sc)
    # new_sc = [service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2,
    #           service_chain.NetworkFunctionName.fun_3]
    # data_base.scs.add_sc(new_sc)
    # data_base.scs.print_all_scs()
    # Network initialize
    data_center = ["0", "10"]
    data_base.add_datacenter(data_center)
    # Traffic generator initialize
    # Para: lambda, mu, request number, optional data size
    data_base.set_traffic_generator(5, 0.001, 2, [1, 3, 5, 7])
    # data_base.tf_gen.print_all_requests()
    # l = data_base.tf_gen.print_sleep_time()
    # x = list(range(1000))
    # pl.hist(l, 10, color='red')
    # pl.scatter(x, l)
    # pl.show()
    # test add vm and vmf
    # data_base.start_new_vm(1, 1, '0')
    # data_base.install_vnf_to_vm(vnf1, data_base.vms[0])
    req1 = data_base.tf_gen.customize_request("1", "10", 0, 1, 1, 20)
    req2 = data_base.tf_gen.customize_request("1", "10", 0, 1, 12, 20)
    # request_process.process_one_req(data_base, data_base.tf_gen.req_set[0])
    # request_process.process_one_req(data_base, data_base.tf_gen.req_set[1])
    request_process.process_one_req(data_base, req1)
    request_process.process_one_req(data_base, req2)





