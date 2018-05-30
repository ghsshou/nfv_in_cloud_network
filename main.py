import service_chain
import traffic_generator
import network_info

if __name__ == "__main__":
    # Initialize the network function information
    function_set = []
    # Function: name, thread, throughput
    new_function = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_1.value, 0, 2)
    function_set.append(new_function)
    new_function = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_2.value, 1, 3)
    function_set.append(new_function)
    new_function = service_chain.NetworkFunction(service_chain.NetworkFunctionName.fun_3.value, 1, 1)
    function_set.append(new_function)
    # Service chain information
    sc_set = service_chain.ServiceChains()
    new_sc = (function_set[0], function_set[1])
    sc_set.add_sc(new_sc)
    new_sc = (function_set[0], function_set[1], function_set[2])
    sc_set.add_sc(new_sc)
    # sc_set.print_all_scs()
    # Network initialize
    data_center = ["0", "10"]
    network_tp = network_info.NetworkInfo(data_center)
    # Traffic generator initialize
    tf_generator = traffic_generator.TrafficGenerator(0.01, 0.001, 100, [1, 3, 5, 7])
    tf_generator.generate_traffic(2, network_tp.get_user_nodes(), 'no')
    # tf_generator.print_all_requests()
    tf_generator.print_sleep_time()




