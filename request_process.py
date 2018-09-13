import network_info as ni
import math
import virtual_layer_elements as vle
import service_chain
import logging
from collections import defaultdict


#
# def process_one_req(data_base, req):
#     print("***************************")
#     print("Now process: ", req)
#     req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the name of vnfs
#     vm_w_vnf = {}
#     est_time = data_base.estimate_start_prc_time(req.arr_time, req.data_size, data_base.scs.get_sc(req.sc))
#     other_vnf_pro_times = []
#     for vnf_type in req_vnfs:
#         print("VNF:" + vnf_type.value[0] + ", ESPT:", est_time[vnf_type])  # ESPT: Estimated start processing time
#         # vnf = data_base.get_instances_of_vnf(vnf_type)
#         # print(vnf)
#         vms = data_base.get_vms_w_vnf(vnf_type)
#         data_base.check_vms_at_time(vms, vnf_type, est_time[vnf_type])
#         if vms:
#             vm_w_vnf[vnf_type] = vms
#             print(vms[0])
#             (process_t, start_t) = data_base.update_vm_w_vnf(vnf_type, vms[0], req.data_size, est_time[vnf_type])
#             print("pro:", process_t, "start_t:", start_t)
#             index = req_vnfs.index(vnf_type)
#             if index < len(req_vnfs) - 1:
#                 next_vnf = req_vnfs[index + 1]
#                 est_time[next_vnf] = start_t + process_t
#                 other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
#             elif index == len(req_vnfs) - 1:
#                 latency = start_t + process_t - req.arr_time
#                 data_base.store_latency(req, latency)
#         else:
#             cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
#             if cpu_core == -1:
#                 data_base.latency[req] = -1
#                 return -1
#             print("CPU_required: " + str(cpu_core))
#             (process_t, start_t) = data_base.start_new_vm(est_time[vnf_type], cpu_core, '0', vnf_type, req.data_size)
#             print("pro:", process_t, "start_t:", start_t)
#             index = req_vnfs.index(vnf_type)
#             if index < len(req_vnfs) - 1:
#                 next_vnf = req_vnfs[index + 1]
#                 est_time[next_vnf] = start_t + process_t
#                 other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
#             elif index == len(req_vnfs) - 1:
#                 latency = start_t + process_t - req.arr_time
#                 data_base.store_latency(req, latency)
#             # data_base.install_vnf_to_vm(vnf_type, new_vm, req.data_size)
#             # print(new_vm)
#             # shut_down_vm_after(data_base, new_vm, 20)


# Estimate time using Eqn. 1, because a new VM will started, the boot time and install time should be considered
def cal_cpu_cores(vnf_type, data_size, ddl, other_vnf_pro_times, ddl_type):
    if vnf_type.value[1] == 0:  # single thread
        return 1
    max_time = ddl - math.ceil(sum(other_vnf_pro_times))
    logging.info("1: Max time left after previous procedures: " + str(max_time))
    max_time -= vle.VirtualMachine.boot_time  # Consider the boot time
    logging.info("2: Max time left after boot a VM: " + str(max_time))
    max_time -= service_chain.NetworkFunction(vnf_type, 0).install_time  # consider the install time of a VNF
    logging.info("3: Max time left after installing an instance: " + str(max_time))
    max_time -= math.ceil(data_size / ni.trans_cap / ni.global_TS)  # consider the egress latency
    logging.info("4: Max time left after transmitting to dst: " + str(max_time))
    if ddl_type == 'fixed':
        max_time = max_time * 0.5
        logging.info("MMMMax time 5: " + str(max_time))
    if max_time <= 0:
        logging.info("**cal_cpu_cores: Request will be blocked due to latency requirement, passed time:"
                     + str(sum(other_vnf_pro_times)) + "DDL:" + str(ddl))
        return -1
    result = math.ceil(data_size / vnf_type.value[2] / (max_time * ni.global_TS))
    if result <= ni.max_cpu_cores:
        if result == 0:
            result = 1
        return result
    else:
        return -1
    # return math.ceil(data_size / vnf_type.value[2] / (max_time * ni.global_TS))


def algorithm_x(data_base, req, scheme):
    logging.info("***************************")
    logging.info("Now process: " + str(req))
    req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the vnfs
    # Update the vnf visit frequency information
    for vnf_type in req_vnfs:
        data_base.vary_vnf_frequency(vnf_type)
    vm_w_vnf = {}
    est_time = data_base.estimate_start_prc_time(req.arr_time, req.data_size, data_base.scs.get_sc(req.sc))
    #  First, get all available VMs at certain time slot
    for vnf_type in req_vnfs:
        logging.info("VNF:" + str(vnf_type.value[0]) + ", ESPT:" + str(est_time[vnf_type]))  # ESPT: Estimated start processing time
        vm_w_vnf[vnf_type] = data_base.get_vms_w_vnf(vnf_type)
        data_base.check_vms_at_time(vm_w_vnf[vnf_type], vnf_type, est_time[vnf_type])
    # Second, check the zone of each VM
    if scheme == 'proposed':
        zones_vnf = defaultdict(list)
        for vnf_type in req_vnfs:
            logging.info("Now find:" + str(vnf_type))
            if vm_w_vnf[vnf_type]:
                zones = []
                for vm in vm_w_vnf[vnf_type]:
                    # print("ALGORITHM_X: Find VM:", vm)
                    zone = data_base.network.get_zone(vm.location)
                    if zone not in zones:
                        zones.append(zone)
                zones_vnf[vnf_type] = zones
        # Third, if there is at least one VNF in a certain zone:
        have_zone_flag = False
        for item in zones_vnf.keys():
            if len(zones_vnf[item]) > 0:
                have_zone_flag = True
        if have_zone_flag:
            # print("ALGORITHM_X: Exist some vnfs already!")
            (best_zone, vnfs_no) = select_best_zone(req_vnfs, zones_vnf)
            logging.info("ALGORITHM_X: best zone:" + str(best_zone) + "max_vnf_no:" + str(vnfs_no))
            # if find a zone hosting at least 2 vnfs, that is best_zone != none
            # print("Find best zone:", best_zone)
            (unmaped_vnfs, mapped_vms) = find_unmapped_vnfs(data_base, req_vnfs, vm_w_vnf, best_zone, scheme)
            place_unmapped_vnfs(data_base, unmaped_vnfs, mapped_vms, req_vnfs, req, est_time, best_zone)

        # if all vnfs have no available instances, we should find a nearest zone to set up VMs to host
        else:
            # print("ALGORITHM_X: Should set up new VMs")
            create_vms_for_sc(req_vnfs, req, data_base, est_time)
    elif scheme == 'conventional':
        conventional_place_vnfs(data_base, req_vnfs, req, est_time, 'Randomized')
    else:
        logging.error("wrong scheme")


# find the vnfs that are not in the zone, return unmapped vnfs, and the vms hosting mapped vnfs in the zone
def find_unmapped_vnfs(data_base, req_vnfs, vm_w_vnf, zone, scheme):
    unmapped_vnf = []
    mapped_vms = {}
    for vnf_type in req_vnfs:
        if not vm_w_vnf[vnf_type]:
            unmapped_vnf.append(vnf_type)
            continue
        else:
            for vm in vm_w_vnf[vnf_type]:
                if scheme == 'conventional':
                    mapped_vms[vnf_type] = vm
                    break
                if data_base.network.get_zone(vm.location) == zone:
                    mapped_vms[vnf_type] = vm
                    break
            unmapped_vnf.append(vnf_type)
    return unmapped_vnf, mapped_vms


# place the unmapped vnfs to complete the service chain
def place_unmapped_vnfs(data_base, unmaped_vnf, mapped_vms, req_vnfs, req, est_time, best_zone):
    logging.info("ALREADY HAVE SOME QUALIFIED VMS!!")
    placed_vms = {}
    other_vnf_pro_times = []
    # if have a best zone, the mapped vms should not be empty, so we get the dc where the vm is installed
    if best_zone:
        cand_dc = list(mapped_vms.values())[0].location
    else:
        (best_zone, cand_dc) = data_base.network.find_nearest_zone(req.src)
        if not cand_dc:
            logging.info("**Error** in fun. placed_unmapped_vnfs: candidate dc calculated failed!")
            return -1
    for vnf_type in req_vnfs:
        index = req_vnfs.index(vnf_type)
        # print("INDEX:", index, "placed_vm:", len(placed_vms))
        # if the vnf has a previous vnf in the chain, which should have been placed
        if vnf_type in unmaped_vnf and index > 0:
            # first, check its previous one
            vm = check_vms_for_vnf(placed_vms[req_vnfs[index - 1]], vnf_type,  req, est_time[vnf_type], data_base)
            if vm:
                logging.info("Previous VM is qualified for VNF:" + str(vnf_type.value[0]) + str(vm))
                # if previous one is found, there is no propagation latency and transmission latency
                # # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", vm.location, "is:",
                # #       pro_latency)
                # # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", vm, "is:",
                # #       tran_latency, ", fee is:", trans_fee)
                install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, vm, req, est_time, other_vnf_pro_times)
                placed_vms[vnf_type] = vm
                continue
            # second, if the previous one cannot be used, then check overall network
            else:
                other_vm = find_nearest_vnf_in_other_zone(vnf_type, data_base, req, est_time)
                if other_vm:
                    logging.info("Find near VM in other zone for VNF:" +  str(vnf_type.value[0]) + str(index) + str(other_vm))
                    pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location,
                                                                other_vm.location)
                    (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                            placed_vms[req_vnfs[index - 1]], other_vm)
                    update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                          placed_vms[req_vnfs[index - 1]].location, other_vm.location)
                    # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", other_vm.location,
                    #       "is:",
                    #       pro_latency)
                    # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", other_vm, "is:",
                    #       tran_latency, ", fee is:", trans_fee)
                    data_base.req_trans_fee[req] += trans_fee
                    est_time[vnf_type] += pro_latency + tran_latency
                    other_vnf_pro_times.append(pro_latency + tran_latency)
                    install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, other_vm, req, est_time,
                                      other_vnf_pro_times)
                    placed_vms[vnf_type] = other_vm
                # If not any VM in other zone is found, we should start a new VM in the candidate data center
                else:
                    pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location,
                                                                cand_dc)
                    (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                            placed_vms[req_vnfs[index - 1]],
                                                                            cand_dc)
                    update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                          placed_vms[req_vnfs[index - 1]].location, cand_dc)
                    # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", new_vm.location,
                    #       "is:",
                    #       pro_latency)
                    # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", new_vm, "is:",
                    #       tran_latency, ", fee is:", trans_fee)
                    data_base.req_trans_fee[req] += trans_fee
                    est_time[vnf_type] += pro_latency + tran_latency
                    other_vnf_pro_times.append(pro_latency + tran_latency)
                    new_vm = create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times,
                                               cand_dc)
                    if not new_vm or new_vm == -1:
                        data_base.req_vm_info[req] = None
                        return None
                    placed_vms[vnf_type] = new_vm
                    logging.info("Start a new VM for VNF:" + str(vnf_type.value[0]) + " " + str(index) + str(new_vm))
        # the first vnf is unmapped
        elif index == 0 and vnf_type in unmaped_vnf:
            other_vm = find_nearest_vnf_in_other_zone(vnf_type, data_base, req, est_time)
            if other_vm:
                logging.info("Find near VM in other zone for VNF:" + str(vnf_type.value[0]) + str(index) + str(other_vm))
                (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                        req.src, other_vm.location)
                # print("propagation latency from", req.src, "to", other_vm.location, "is:", pro_latency)
                # print("transmission latency from", req.src, "to", other_vm, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, other_vm, req, est_time, other_vnf_pro_times)
                placed_vms[vnf_type] = other_vm
            else:
                (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                        req.src, cand_dc)
                # print("propagation latency from", req.src, "to", cand_dc, "is:", pro_latency)
                # print("transmission latency from", req.src, "to", cand_dc, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                new_vm = create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times,
                                           cand_dc)
                if not new_vm or new_vm == -1:
                    data_base.req_vm_info[req] = None
                    return None
                placed_vms[vnf_type] = new_vm
                logging.info("Start a new VM for VNF:" + str(vnf_type.value[0]) + " index: " + str(index) + " " + str(new_vm))
        # have found suitable VM to host.
        else:
            vm = mapped_vms[vnf_type]
            logging.info("Have a suitable VM for VNF:" + str(vnf_type.value[0]) + str(index) + str(vm))
            # if it is the first vnf, there is a transmission latency and
            # propagation latency from the Internet to the vm
            if index == 0:
                (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                        req.src, vm.location)
                # print("propagation latency from", req.src, "to", vm.location, "is:", pro_latency)
                # print("transmission latency from", req.src, "to", vm, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
            # if it is not the first vnf, there is a transmission latency and
            # propagation latency between the previous one and the later one
            else:
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, vm.location)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]], vm)
                update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                      placed_vms[req_vnfs[index - 1]].location, vm.location)
                # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", vm.location, "is:",
                #       pro_latency)
                # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", vm, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
            install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, vm, req, est_time, other_vnf_pro_times)
            placed_vms[vnf_type] = vm
            continue
    data_base.req_vm_info[req] = placed_vms


# place the unmapped vnfs to complete the service chain
def conventional_place_vnfs(data_base, req_vnfs, req, est_time, sel_way='Greedy'):
    placed_vms = {}
    other_vnf_pro_times = []
    # if have a best zone, the mapped vms should not be empty, so we get the dc where the vm is installed
    (best_zone, cand_dc) = data_base.network.find_nearest_zone(req.src)
    # check all available vms in the network
    vm_w_vnf = {}
    for vnf_type in req_vnfs:
        index = req_vnfs.index(vnf_type)
        vm_w_vnf[vnf_type] = data_base.get_vms_w_vnf(vnf_type)
        data_base.check_vms_at_time(vm_w_vnf[vnf_type], vnf_type, est_time[vnf_type])
        # if there is at least one qualified VM
        if vm_w_vnf[vnf_type]:
            if index == 0:
                # find the zone nearest to the last one
                vm = vm_w_vnf[vnf_type][0]
                if sel_way == 'Greedy':
                    if len(vm_w_vnf[vnf_type]) > 0:
                        for var_vm in vm_w_vnf[vnf_type]:
                            if data_base.network.get_zone(var_vm.location) == data_base.network.get_zone(
                                    cand_dc):
                                vm = var_vm
                                break

                (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                        req.src, vm.location)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
            else:
                # find the zone nearest to the last one
                vm = vm_w_vnf[vnf_type][0]
                if sel_way == 'Greedy':
                    if len(vm_w_vnf[vnf_type]) > 0:
                        for var_vm in vm_w_vnf[vnf_type]:
                            if data_base.network.get_zone(var_vm.location) == data_base.network.get_zone(
                                    placed_vms[req_vnfs[index - 1]].location):
                                vm = var_vm
                                break
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, vm.location)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]], vm)
                update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                      placed_vms[req_vnfs[index - 1]].location, vm.location)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
            install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, vm, req, est_time, other_vnf_pro_times)
            placed_vms[vnf_type] = vm
            continue
        # no available VMs, so a new VM is started
        else:
            if index == 0:
                (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                        req.src, cand_dc)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                new_vm = create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times,
                                           cand_dc)
                if not new_vm or new_vm == -1:
                    data_base.req_vm_info[req] = None
                    return None
                placed_vms[vnf_type] = new_vm
                logging.info("Start a new VM for VNF:" + str(vnf_type.value[0]) + str(index) + str(new_vm))
            else:
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location,
                                                            cand_dc)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]],
                                                                        cand_dc)
                update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                      placed_vms[req_vnfs[index - 1]].location, cand_dc)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                new_vm = create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times,
                                           cand_dc)
                if not new_vm or new_vm == -1:
                    data_base.req_vm_info[req] = None
                    return None
                placed_vms[vnf_type] = new_vm
                logging.info("Start a new VM for VNF:" + str(vnf_type.value[0]) + str(index) + str(new_vm))
    data_base.req_vm_info[req] = placed_vms


# install a vnf to a VM and update the time
def install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, vm, req, est_time, other_vnf_pro_times):
    (process_t, start_t) = data_base.update_vm_w_vnf(vnf_type, vm, req.data_size, est_time[vnf_type])
    # print("pro:", process_t, "start_t:", start_t)
    # print(vm)
    if index < len(req_vnfs) - 1:
        next_vnf = req_vnfs[index + 1]
        est_time[next_vnf] = start_t + process_t
        other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
    elif index == len(req_vnfs) - 1:
        latency = start_t + process_t - req.arr_time
        logging.info("SSS,start:" + str(start_t) + "process:" + str(process_t))
        # there are transmission latency and propagation latency from the last vm location to the dst node
        (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, vm.location, req.dst)
        latency += pro_latency + trans_latency
        logging.info("prolan:" + str(pro_latency) + "trans:" + str(trans_latency))
        data_base.req_trans_fee[req] += fee
        # print("XXXX", latency)
        data_base.store_latency(req, latency)


# create a VM for a VNF
def create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times, cand_dc):
    temp_ddl = req.deadline
    if req.ddl_type == data_base.tf_gen.ddl_type_list[1]:  # variable
        temp_ddl = req.deadline[1]
    cpu_core = cal_cpu_cores(vnf_type, req.data_size, temp_ddl, other_vnf_pro_times, req.ddl_type)
    logging.info("CPU_required: " + str(cpu_core))
    if cpu_core == -1:
        data_base.store_latency(req, float('inf'))
        return None
    if len(data_base.vms) > data_base.max_vms_online:
        data_base.store_latency(req, float('inf'))
        return None
    # below, is for the case that we start a VM before the data arrives it, to minimize the latency
    extra_time = 0
    extra_time += vle.VirtualMachine.boot_time + service_chain.NetworkFunction(vnf_type, 0).install_time
    if extra_time >= est_time[vnf_type]:
        extra_time = est_time[vnf_type]
    (process_t, start_t, new_vm) = data_base.start_new_vm(est_time[vnf_type] - extra_time, cpu_core, cand_dc, vnf_type,
                                                          req.data_size)
    # # if it is the first vnf, there is a propagation latency and transmission latency from the src to the vm location
    # if index == 0:
    #     pro_latency = data_base.propagation_latency(req.src, )
    # now, update time
    # print("pro:", process_t, "start_t:", start_t)
    if index < len(req_vnfs) - 1:
        next_vnf = req_vnfs[index + 1]
        est_time[next_vnf] = start_t + process_t
        other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
    elif index == len(req_vnfs) - 1:
        latency = start_t + process_t - req.arr_time
        # there are transmission latency and propagation latency from the last vm location to the dst node
        (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, new_vm.location, req.dst)
        latency += pro_latency + trans_latency
        data_base.req_trans_fee[req] += fee
        # print("XXXX", latency)
        data_base.store_latency(req, latency)
    return new_vm


# find the nearest available VM in other zone, which should be qualified
def find_nearest_vnf_in_other_zone(vnf_type, data_base, req, est_time):
    vms = data_base.get_vms_w_vnf(vnf_type)
    data_base.check_vms_at_time(vms, vnf_type, est_time[vnf_type])
    short_dis = float('inf')
    near_vm = None
    for vm in vms:
        install_time = 0
        if not vm.host_vnf(vnf_type):
            install_time += service_chain.NetworkFunction(vnf_type, 0).install_time
        process_time = math.ceil(req.data_size / (vm.cpu_cores * vnf_type.value[2]) / ni.global_TS)
        actual_start = vm.get_next_ava_time()
        if actual_start < est_time[vnf_type]:
            actual_start = est_time[vnf_type]
        pro_latency = data_base.propagation_latency(vm.location, req.dst)
        temp_ddl = req.deadline
        if req.ddl_type == data_base.tf_gen.ddl_type_list[1]:  # variable ddl
            temp_ddl = req.deadline[1]
        if actual_start + process_time + install_time + math.ceil(req.data_size / ni.trans_cap / ni.global_TS) \
                + pro_latency < temp_ddl + req.arr_time:
            if data_base.network.get_shortest_dis(req.src, vm.location) < short_dis:
                near_vm = vm
                short_dis = data_base.network.get_shortest_dis(req.src, vm.location)
    return near_vm


# Create vms for all VNFs
def create_vms_for_sc(req_vnfs, req, data_base, est_time):
    logging.info("CREATE NEW VMS FOR ALL VNFS!")
    other_vnf_pro_times = []
    (cand_zone, cand_dc) = data_base.network.find_nearest_zone(req.src)
    # print("Create VM in DC:", cand_dc, "located in zone:", cand_zone)
    created_vms = []
    placed_vms = {}
    for vnf_type in req_vnfs:
        # print("CREATE_VMS_FOR_SC:", vnf_type)
        index = req_vnfs.index(vnf_type)
        if 0 < index < len(req_vnfs):
            vm = check_vms_for_vnf(created_vms, vnf_type, req, est_time[vnf_type], data_base)
            # if we get a vm that is suit for the current VNF
            if vm:
                logging.info("Find a VM for VNF: " + str(vnf_type.value[0]) + str(vm))
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, vm.location)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]], vm)
                update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                      placed_vms[req_vnfs[index - 1]].location, vm.location)
                # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", vm.location, "is:",
                #       pro_latency)
                # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", vm, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                install_vnf_to_vm(data_base, index, vnf_type, req_vnfs, vm, req, est_time, other_vnf_pro_times)
                # (process_t, start_t) = data_base.update_vm_w_vnf(vnf_type, vm, req.data_size, est_time[vnf_type])
                placed_vms[vnf_type] = vm
                # print("pro:", process_t, "start_t:", start_t)
                # print(vm)
                # if index < len(req_vnfs) - 1:
                #     next_vnf = req_vnfs[index + 1]
                #     est_time[next_vnf] = start_t + process_t
                #     other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
                # elif index == len(req_vnfs) - 1:
                #     latency = start_t + process_t - req.arr_time
                    # there are transmission latency and propagation latency from the last vm location to the dst node
                    # (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, vm.location,
                    #                                                                    req.dst)
                    # latency += pro_latency + trans_latency
                    # data_base.req_trans_fee[req] += fee
                    # print("XXXX", latency)
                    # data_base.store_latency(req, latency)
                continue
            else:
                # if no qualified vm, a new VM should be set up
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, cand_dc)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]], cand_dc)
                update_FS_consumption(data_base, placed_vms[req_vnfs[index - 1]].cpu_cores,
                                      placed_vms[req_vnfs[index - 1]].location, cand_dc)
                # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", vm.location, "is:",
                #       pro_latency)
                # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", vm, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                new_vm = create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times,
                                           cand_dc)
                if not new_vm or new_vm == -1:
                    data_base.req_vm_info[req] = None
                    return None
                placed_vms[vnf_type] = new_vm
                created_vms.append(new_vm)
                logging.info("Start a new VM for VNF:" + str(vnf_type.value[0]) + str(index) + str(new_vm))
                # cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
                # print("CPU_required: " + str(cpu_core))
                # if cpu_core == -1:
                #     data_base.req_vm_info[req] = None
                #     return None
                # (process_t, start_t, new_vm) = data_base.start_new_vm(est_time[vnf_type], cpu_core, cand_dc, vnf_type,
                #                                                       req.data_size)
                # created_vms.append(new_vm)
                # placed_vms[vnf_type] = new_vm
                # print(str(index), new_vm)
                # print("pro:", process_t, "start_t:", start_t)
                # if index < len(req_vnfs) - 1:
                #     next_vnf = req_vnfs[index + 1]
                #     est_time[next_vnf] = start_t + process_t
                #     other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
                # elif index == len(req_vnfs) - 1:
                #     latency = start_t + process_t - req.arr_time
                #     # there are transmission latency and propagation latency from the last vm location to the dst node
                #     (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, new_vm.location,
                #                                                                        req.dst)
                #     latency += pro_latency + trans_latency
                #     data_base.req_trans_fee[req] += fee
                #     # print("XXXX", latency)
                #     data_base.store_latency(req, latency)
        # index = 0
        else:
            (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                    req.src, cand_dc)
            logging.info("propagation latency from" + str(req.src) + "to" + str(cand_dc) + "is:" + str(pro_latency))
            logging.info("transmission latency from" + str(req.src) + "to" + str(cand_dc) + "is:" +
                  str(tran_latency) + ", fee is:" + str(trans_fee))
            data_base.req_trans_fee[req] += trans_fee
            est_time[vnf_type] += pro_latency + tran_latency
            other_vnf_pro_times.append(pro_latency + tran_latency)
            new_vm = create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times,
                                       cand_dc)
            if not new_vm or new_vm == -1:
                data_base.req_vm_info[req] = None
                return None
            placed_vms[vnf_type] = new_vm
            created_vms.append(new_vm)
            logging.info("Start a new VM for VNF:" + str(vnf_type.value[0]) + str(index) + str(new_vm))
            # cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
            # print("CPU_required: " + str(cpu_core))
            # if cpu_core == -1:
            #     data_base.req_vm_info[req] = None
            #     return None
            # (process_t, start_t, new_vm) = data_base.start_new_vm(est_time[vnf_type], cpu_core, cand_dc, vnf_type,
            #                                                       req.data_size)
            # created_vms.append(new_vm)
            # placed_vms[vnf_type] = new_vm
            # print(str(index), new_vm)
    data_base.req_vm_info[req] = placed_vms


# Check if there is any qualified VM in the set to run a VNF
def check_vms_for_vnf(vms, vnf_type, req, vnf_start_time, data_base):
    if not vms:
        return None
    # below is for the case that 'vms' is a vm, not a list of vms
    if not isinstance(vms, list):
        new_vms = []
        new_vms.append(vms)
        vms = new_vms
    cand_vms = []
    if vnf_type.value[1] == 0:  # single thread
        for vm in vms:
            if vm.cpu_cores == 1:
                return vm
    else:
        for vm in vms:
            install_time = 0
            # if the vm has already installed such a vnf, no installation is needed
            if not vm.host_vnf(vnf_type):
                install_time += service_chain.NetworkFunction(vnf_type, 0).install_time
            process_time = math.ceil(req.data_size / (vm.cpu_cores * vnf_type.value[2]) / ni.global_TS)
            # if the estimated start processing time of a VNF plus processing time and install time is less than the
            # required finish time, then the VM is possible to be qualified. But, because the actual start processing
            # time might be later than the value of 'est_time[vnf_type]', the actual consumed time is still longer than
            # the DDL requirement. To minimize the case, the transmission latency (from last VM's location to dst node)
            # is considered
            actual_start = vm.get_next_ava_time()
            if actual_start < vnf_start_time:
                actual_start = vnf_start_time
            pro_latency = data_base.propagation_latency(vm.location, req.dst)
            temp_ddl = req.deadline
            if req.ddl_type == data_base.tf_gen.ddl_type_list[1]:  # variable
                temp_ddl = req.deadline[1]
            if actual_start + process_time + install_time + math.ceil(req.data_size / ni.trans_cap / ni.global_TS)\
                    + pro_latency < temp_ddl + req.arr_time:
                cand_vms.append(vm)
    final_vm = None
    cpu_cores = 0
    for vm in cand_vms:
        if cpu_cores < vm.cpu_cores:
            cpu_cores = vm.cpu_cores
            final_vm = vm
    return final_vm


#  Given a set of zones, whose key is vnf_type, return the best zone should selected, and how many vnfs in this zone
def select_best_zone(req_vnfs, zones_vnf):
    # Construct a matrix, of which the column is the zone, and the row is the vnf
    # if a vnf has an instance in a zone, the value is 1, otherwise, the value is 0
    zone_bit_and_sum = {}
    for zone in ni.CPUPrice:
        temp_sum = 0
        for i in range(len(req_vnfs) - 1):
            if zone.value[0] in zones_vnf[req_vnfs[i]] and zone.value[0] in zones_vnf[req_vnfs[i + 1]]:
                temp_sum += 1
        zone_bit_and_sum[zone.value[0]] = temp_sum
    max_value = 0
    max_zone = None
    for zone in zone_bit_and_sum:
        if zone_bit_and_sum[zone] > max_value:
            max_value = zone_bit_and_sum[zone]
            max_zone = zone
    if max_zone:
        max_value += 1  # because the value is the sum of two adjacent vnfs
    return max_zone, max_value


# used to calculate the FS allocated
def update_FS_consumption(data_base, cpu_cores, src, dst):
    hop = data_base.get_hop(src, dst)
    # fs_no = math.ceil(cpu_cores * ni.basic_trans_capacity / ni.cap_one_FS) * hop
    fs_no = 0
    data_base.used_FS += fs_no

# This function is used to find the set of vms which are available at certain time slot,
# considering the processing latency of each VNF
# def get_qualified_vms(data_base, req):


