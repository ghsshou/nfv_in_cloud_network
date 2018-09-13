import service_chain
import network_info
import data_base as db
import request_process
import time
import numpy as np
import os
import shutil
import logging
import sys

LOG_FILE = 'details_log.log'


# run simulation once
def run_simulation_once(lmd, ddl_scale, traffic_num, traffic_size_scale):
    # Get a database
    data_base = db.DataBase()
    # Initialize the network function information
    new_sc = [service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2
              ]
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_3, service_chain.NetworkFunctionName.fun_4,
              service_chain.NetworkFunctionName.fun_5)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_5,
              service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_2, service_chain.NetworkFunctionName.fun_5,
              service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_2,
              service_chain.NetworkFunctionName.fun_3, service_chain.NetworkFunctionName.fun_4,
              service_chain.NetworkFunctionName.fun_5)
    data_base.scs.add_sc(new_sc)
    new_sc = (service_chain.NetworkFunctionName.fun_1, service_chain.NetworkFunctionName.fun_3,
              service_chain.NetworkFunctionName.fun_5, service_chain.NetworkFunctionName.fun_4)
    data_base.scs.add_sc(new_sc)
    # data_base.scs.print_all_scs()
    # Network initialize
    # data_center = ["6", "17", "22"]
    data_center = ["1", "13", "19", "26"]
    data_base.add_datacenter(data_center)
    # Traffic generator initialize
    # Para: lambda, mu, request number, optional data size
    traffic_size = np.array([7, 8, 9, 10])
    traffic_size = traffic_size * traffic_size_scale
    traffic_size = list(traffic_size)
    (avg_arr, due_time) = data_base.set_traffic_generator(lmd, ddl_scale, traffic_num, traffic_size)
    # print("Finish: ", end="")
    for i in range(traffic_num):
        sys.stdout.write("\r" + str(round((i + 1) / traffic_num * 100, 4)) + "%")
        # request_process.process_one_req(data_base, data_base.tf_gen.req_set[i])
        request_process.algorithm_x(data_base, data_base.tf_gen.req_set[i], 'conventional')
        # time.sleep(data_base.tf_gen.sleep_time[i] * network_info.global_TS * data_base.tf_gen.control_factor)
    # time.sleep(3)
    print()
    (cpu_cost, trans_cost) = data_base.get_cost()
    used_vm = data_base.get_used_vm_no()
    data_base.print_req_provisioning()
    # print("Average Latency: " + str(round(data_base.average_latency(), 3)) + "s")
    # print("Average Arrival Interval: " + str(round(avg_arr, 3)))
    # print("Traffic Load:" + str(round(data_base.average_latency() / avg_arr, 3)))
    # print("BP: " + str(data_base.blocking_probability() * 100) + "%")
    # print("Used FS:" + str(data_base.used_FS))
    # data_base.print_all_vms()
    data_base.reset_counters()
    # 0 cpu_cost, 1 tran_cost, 2 used vms, 3 latency, 4 average arrival, 5 traffic load, 6, bp 7 used fss,
    # 8 theory traffic load
    return cpu_cost, trans_cost, used_vm, data_base.average_latency(), avg_arr, \
        data_base.average_latency() / avg_arr, data_base.blocking_probability(), data_base.used_FS, due_time / avg_arr


# run with parameter lambda
def run_simulation_w_lambda(lmd, ddl_scale, simu_time, traffic_num, traffic_size_scale):
    # print("Finish: \t 0%")
    # initialize the simulation environment
    cpu_cost_rec = []
    trans_cost_rec = []
    vm_used_rec = []
    latency_rec = []
    arr_time_rec = []
    tf_load_rec = []
    bp_rec = []
    used_fs_rec = []
    theory_tf_load = []
    total_cost = []
    simulation_time = simu_time
    for i in range(simulation_time):
        print("Round " + str(i+1) + ":")
        result = run_simulation_once(lmd, ddl_scale, traffic_num, traffic_size_scale)
        # 0 cpu_cost, 1 tran_cost, 2 used vms, 3 latency, 4 average arrival, 5 traffic load, 6, bp 7 used fss
        cpu_cost_rec.append(result[0])
        trans_cost_rec.append(result[1])
        vm_used_rec.append(result[2])
        latency_rec.append(result[3])
        arr_time_rec.append(result[4])
        tf_load_rec.append(result[5])
        bp_rec.append(result[6])
        used_fs_rec.append(result[7])
        theory_tf_load.append(result[8])
        total_cost.append(result[0] + result[1])
    results = {}  # each element is (mean, std) for 0: traffic load, 1: cpu cost, 2: bp, 3: latency, 4: used vms,
    # 5: used fss, 6 arrival interval, 7 traffic load in theory, 8 trans. cost, 9 total cost
    avg_cpu_cost = np.mean(cpu_cost_rec)
    std_cpu_cost = np.std(cpu_cost_rec)
    results['[1] CPU_Cost'] = (avg_cpu_cost, std_cpu_cost)
    avg_trans_cost = np.mean(trans_cost_rec)
    std_trans_cost = np.std(trans_cost_rec)
    results['[8] Trans_Cost'] = (avg_trans_cost, std_trans_cost)
    avg_total_cost = np.mean(total_cost)
    std_total_cost = np.std(total_cost)
    results['[9] Total_Cost'] = (avg_total_cost, std_total_cost)
    avg_vm = np.mean(vm_used_rec)
    std_vm = np.std(vm_used_rec)
    results['[4] Used_VM'] = (avg_vm, std_vm)
    avg_latency = np.mean(latency_rec)
    std_latency = np.std(latency_rec)
    results['[3] Latency'] = (avg_latency, std_latency)
    avg_arr = np.mean(arr_time_rec)
    std_arr = np.std(arr_time_rec)
    results['[6] Arr._Int'] = (avg_arr, std_arr)
    avg_tf_load = np.mean(tf_load_rec)
    std_tf_load = np.std(tf_load_rec)
    results['[0] Traffic_Load'] = (avg_tf_load, std_tf_load)
    avg_bp = np.mean(bp_rec)
    std_bp = np.std(bp_rec)
    results['[2] BP'] = (avg_bp, std_bp)
    avg_fs = np.mean(used_fs_rec)
    std_fs = np.std(used_fs_rec)
    results['[5] Used_FSs'] = (avg_fs, std_fs)
    avg_theo_load = np.mean(theory_tf_load)
    std_theo_load = np.std(theory_tf_load)
    results['[7] Theory_Traffic_Load '] = (avg_theo_load, std_theo_load)

    print(" ".ljust(15) + "Mean".ljust(10) + "STD")
    print("Traffic Load:".ljust(15) + str(round(avg_tf_load, 2)).ljust(10) + str(round(std_tf_load, 2)))
    print("CPU Cost:".ljust(15) + str(round(avg_cpu_cost, 2)).ljust(10) + str(round(std_cpu_cost, 2)))
    print("Trans. Cost:".ljust(15) + str(round(avg_trans_cost, 2)).ljust(10) + str(round(std_trans_cost, 2)))
    print("Total Cost:".ljust(15) + str(round(avg_total_cost, 2)).ljust(10) + str(round(std_total_cost, 2)))
    print("BP:".ljust(15) + str(round(avg_bp, 4)).ljust(10) + str(round(std_bp, 4)))
    print("Latency:".ljust(15) + str(round(avg_latency, 2)).ljust(10) + str(round(std_latency, 2)))
    print("Used VM:".ljust(15) + str(round(avg_vm, 2)).ljust(10) + str(round(std_vm, 2)))
    print("Used FSs:".ljust(15) + str(round(avg_fs, 2)).ljust(10) + str(round(std_fs, 2)))
    print("Arr. Int.:".ljust(15) + str(round(avg_arr, 2)).ljust(10) + str(round(std_arr, 2)))
    return results


# output parameters and results to file
def output_to_file(pars, results, file_name):
    with open(file_name, 'a') as f:
        f.write("@ Simulation Parameters: ")
        for item in pars:
            f.write(item + ": " + str(pars[item]))
        f.write("\n".ljust(20) + "Mean".ljust(10) + "STD\n")
        # to output in order
        names = list(results.keys())
        names.sort()
        for item in names:
            accuracy = 2
            if 'BP' in item:
                accuracy = 4
            f.write(item.ljust(20) + str(round(results[item][0], accuracy)).ljust(10) +
                    str(round(results[item][1], accuracy)) + "\n")
            # os.makedirs('results')
            sub_file_name = 'results//' + item.split()[1] + '.txt'
            with open(sub_file_name, 'a') as ff:
                ff.write(
                    str(round(results[item][0], accuracy)).ljust(10) + str(round(results[item][1], accuracy)) + '\n')


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.WARNING, filemode='w', format='%(message)s')
    shutil.rmtree("results")
    os.mkdir("results")
    lmd_set = [0.04, 0.05, 0.06, 0.07, 0.08]
    # lmd_set = [0.01, 0.011, 0.0125, 0.015, 0.0167, 0.02, 0.025, 0.033, 0.05, 0.1]  # for different lambda
    # ddl_scale_set = [1, 1.5, 2]  # for different ddl
    traffic_size_scale = [0.15, 0.225, 0.3, 0.375, 0.45, 0.525, 0.6, 0.675, 0.75]
    traffic_size_scale = [0.75]
    simulation_time = 10
    traffic_num = 10000
    file_name = 'results.txt'
    if os.path.exists(file_name):
        os.remove(file_name)
    parameters = {}
    logging.info("Simulation begins")
    # for lmd in lmd_set:
    #     results = run_simulation_w_lambda(lmd, 0.92, simulation_time, traffic_num, 0.2)
    #     parameters['lambda'] = lmd
    #     output_to_file(parameters, results, file_name)
    start_time = time.time()
    for tf in traffic_size_scale:
        print("data size:", tf)
        results = run_simulation_w_lambda(0.05, 0.93, simulation_time, traffic_num, tf)
        parameters['traffic size'] = tf
        output_to_file(parameters, results, file_name)
        print("elapsed time: " + str(time.time() - start_time))
        start_time = time.time()
