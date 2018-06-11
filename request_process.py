import threading
import network_info as ni
import math
import virtual_layer_elements as vle
import service_chain
from collections import defaultdict


def process_one_req(data_base, req):
    print("***************************")
    print("Now process: ", req)
    req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the name of vnfs
    vm_w_vnf = {}
    est_time = data_base.estimate_start_prc_time(req.arr_time, req.data_size, data_base.scs.get_sc(req.sc))
    other_vnf_pro_times = []
    for vnf_type in req_vnfs:
        print("VNF:" + vnf_type.value[0] + ", ESPT:", est_time[vnf_type])  # ESPT: Estimated start processing time
        # vnf = data_base.get_instances_of_vnf(vnf_type)
        # print(vnf)
        vms = data_base.get_vms_w_vnf(vnf_type)
        data_base.check_vms_at_time(vms, vnf_type, est_time[vnf_type])
        if vms:
            vm_w_vnf[vnf_type] = vms
            print(vms[0])
            (process_t, start_t) = data_base.update_vm_w_vnf(vnf_type, vms[0], req.data_size, est_time[vnf_type])
            print("pro:", process_t, "start_t:", start_t)
            index = req_vnfs.index(vnf_type)
            if index < len(req_vnfs) - 1:
                next_vnf = req_vnfs[index + 1]
                est_time[next_vnf] = start_t + process_t
                other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
            elif index == len(req_vnfs) - 1:
                latency = start_t + process_t - req.arr_time
                data_base.store_latency(req, latency)
        else:
            cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
            print("CPU_required: " + str(cpu_core))
            (process_t, start_t) = data_base.start_new_vm(est_time[vnf_type], cpu_core, '0', vnf_type, req.data_size)
            print("pro:", process_t, "start_t:", start_t)
            index = req_vnfs.index(vnf_type)
            if index < len(req_vnfs) - 1:
                next_vnf = req_vnfs[index + 1]
                est_time[next_vnf] = start_t + process_t
                other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
            elif index == len(req_vnfs) - 1:
                latency = start_t + process_t - req.arr_time
                data_base.store_latency(req, latency)
            # data_base.install_vnf_to_vm(vnf_type, new_vm, req.data_size)
            # print(new_vm)
            # shut_down_vm_after(data_base, new_vm, 20)


# Estimate time using Eqn. 1, because a new VM will started, the boot time and install time should be considered
def cal_cpu_cores(vnf_type, data_size, ddl, other_vnf_pro_times):
    if vnf_type.value[1] == 0:  # single thread
        return 1
    max_time = ddl - sum(other_vnf_pro_times)
    max_time -= vle.VirtualMachine.boot_time  # Consider the boot time
    max_time -= service_chain.NetworkFunction(vnf_type).install_time  # consider the install time of a VNF
    if max_time < 0:
        print("**cal_cpu_cores: Request will be blocked due to latency requirement, passed time:",
              sum(other_vnf_pro_times), "DDL:", ddl)
        return -1
    return math.ceil(data_size / vnf_type.value[2] / (max_time * ni.global_TS))


def algorithm_x(data_base, req):
    print("***************************")
    print("Now process: ", req)
    req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the name of vnfs
    vm_w_vnf = {}
    est_time = data_base.estimate_start_prc_time(req.arr_time, req.data_size, data_base.scs.get_sc(req.sc))
    #  First, get all available VMs at certain time slot
    for vnf_type in req_vnfs:
        # print("VNF:" + vnf_type.value[0] + ", ESPT:", est_time[vnf_type])  # ESPT: Estimated start processing time
        vm_w_vnf[vnf_type] = data_base.get_vms_w_vnf(vnf_type)
        data_base.check_vms_at_time(vm_w_vnf[vnf_type], vnf_type, est_time[vnf_type])
    # Second, check the zone of each VM
    zones_vnf = defaultdict(list)
    for vnf_type in req_vnfs:
        # print("Now find:", vnf_type)
        if vm_w_vnf[vnf_type]:
            zones = []
            for vm in vm_w_vnf[vnf_type]:
                # print("ALGORITHM_X: Find VM:", vm)
                zone = data_base.network.get_zone(vm.location)
                zones.append(zone)
            zones_vnf[vnf_type] = zones
    # Third, if there is at least one VNF in a certain zone:
    if zones_vnf:
        # print("ALGORITHM_X: Exist some vnfs already!")
        (best_zone, vnfs_no) = select_best_zone(req_vnfs, zones_vnf)
        # print("ALGORITHM_X: best zone:", best_zone, "max_vnf_no:", vnfs_no)
        # if find a zone hosting at least 2 vnfs, that is best_zone != none
        # print("Find best zone:", best_zone)
        (unmaped_vnfs, mapped_vms) = find_unmapped_vnfs(data_base, req_vnfs, vm_w_vnf, best_zone)
        place_unmapped_vnfs(data_base, unmaped_vnfs, mapped_vms, req_vnfs, req, est_time, best_zone)

    # if all vnfs have no available instances, we should find a nearest zone to set up VMs to host
    else:
        # print("ALGORITHM_X: Should set up new VMs")
        create_vms_for_sc(req_vnfs, req, data_base, est_time)


# find the vnfs that are not in the zone, return unmapped vnfs, and the vms hosting mapped vnfs in the zone
def find_unmapped_vnfs(data_base, req_vnfs, vm_w_vnf, zone):
    unmapped_vnf = []
    mapped_vms = {}
    for vnf_type in req_vnfs:
        if not vm_w_vnf[vnf_type]:
            unmapped_vnf.append(vnf_type)
            continue
        else:
            for vm in vm_w_vnf[vnf_type]:
                if data_base.network.get_zone(vm.location) == zone:
                    mapped_vms[vnf_type] = vm
                    break
            unmapped_vnf.append(vnf_type)
    return unmapped_vnf, mapped_vms


# place the unmapped vnfs to complete the service chain
def place_unmapped_vnfs(data_base, unmaped_vnf, mapped_vms, req_vnfs, req, est_time, best_zone):
    placed_vms = {}
    other_vnf_pro_times = []
    # if have a best zone, the mapped vms should not be empty, so we get the dc where the vm is installed
    if best_zone:
        cand_dc = list(mapped_vms.values())[0].location
    else:
        (best_zone, cand_dc) = data_base.network.find_nearest_zone(req.src)
        if not cand_dc:
            print("**Error** in fun. placed_unmapped_vnfs: candidate dc calculated failed!")
            return -1
    for vnf_type in req_vnfs:
        index = req_vnfs.index(vnf_type)
        # print("INDEX:", index, "placed_vm:", len(placed_vms))
        # if the vnf has a previous vnf in the chain, which should have been placed
        if vnf_type in unmaped_vnf and index > 0:
            # first, check its previous one
            vm = check_vms_for_vnf(placed_vms[req_vnfs[index - 1]], vnf_type, est_time, req)
            if vm:
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, vm.location)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]], vm)
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
            # second, if the previous one cannot be used, then check overall network
            else:
                other_vm = find_nearest_vnf_in_other_zone(vnf_type, data_base, req, est_time)
                if other_vm:
                    pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location,
                                                                other_vm.location)
                    (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                            placed_vms[req_vnfs[index - 1]], other_vm)
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
                else:
                    pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location,
                                                                new_vm.location)
                    (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                            placed_vms[req_vnfs[index - 1]],
                                                                            new_vm)
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
                    placed_vms[vnf_type] = new_vm

        # the first vnf is unmapped
        elif index == 0 and vnf_type in unmaped_vnf:
            other_vm = find_nearest_vnf_in_other_zone(vnf_type, data_base, req, est_time)
            if other_vm:
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
                placed_vms[vnf_type] = new_vm

        # have found suitable VM to host.
        else:
            vm = mapped_vms[vnf_type]
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
        # there are transmission latency and propagation latency from the last vm location to the dst node
        (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, vm.location, req.dst)
        latency += pro_latency + trans_latency
        data_base.req_trans_fee[req] += fee
        data_base.store_latency(req, latency)


# create a VM for a VNF
def create_vm_for_vnf(data_base, index, vnf_type, req_vnfs, req, est_time, other_vnf_pro_times, cand_dc):
    cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
    # print("CPU_required: " + str(cpu_core))
    (process_t, start_t, new_vm) = data_base.start_new_vm(est_time[vnf_type], cpu_core, cand_dc, vnf_type,
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
        data_base.store_latency(req, latency)
    return new_vm


# find the nearest available VM in other zone
def find_nearest_vnf_in_other_zone(vnf_type, data_base, req, est_time):
    vms = data_base.get_vms_w_vnf(vnf_type)
    data_base.check_vms_at_time(vms, vnf_type, est_time[vnf_type])
    short_dis = float('inf')
    near_vm = None
    for vm in vms:
        if data_base.network.get_shortest_dis(req.src, vm.location) < short_dis:
            near_vm = vm
            short_dis = data_base.network.get_shortest_dis(req.src, vm.location)
    return near_vm


# Create vms for all VNFs
def create_vms_for_sc(req_vnfs, req, data_base, est_time):
    other_vnf_pro_times = []
    (cand_zone, cand_dc) = data_base.network.find_nearest_zone(req.src)
    # print("Create VM in DC:", cand_dc, "located in zone:", cand_zone)
    created_vms = []
    placed_vms = {}
    for vnf_type in req_vnfs:
        # print("CREATE_VMS_FOR_SC:", vnf_type)
        index = req_vnfs.index(vnf_type)
        if 0 < index < len(req_vnfs):
            vm = check_vms_for_vnf(created_vms, vnf_type, est_time, req)
            # if we get a vm that is suit for the current VNF
            if vm:
                pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, vm.location)
                (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                        placed_vms[req_vnfs[index - 1]], vm)
                # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", vm.location, "is:",
                #       pro_latency)
                # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", vm, "is:",
                #       tran_latency, ", fee is:", trans_fee)
                data_base.req_trans_fee[req] += trans_fee
                est_time[vnf_type] += pro_latency + tran_latency
                other_vnf_pro_times.append(pro_latency + tran_latency)
                (process_t, start_t) = data_base.update_vm_w_vnf(vnf_type, vm, req.data_size, est_time[vnf_type])
                placed_vms[vnf_type] = vm
                # print("pro:", process_t, "start_t:", start_t)
                # print(vm)
                if index < len(req_vnfs) - 1:
                    next_vnf = req_vnfs[index + 1]
                    est_time[next_vnf] = start_t + process_t
                    other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
                elif index == len(req_vnfs) - 1:
                    latency = start_t + process_t - req.arr_time
                    # there are transmission latency and propagation latency from the last vm location to the dst node
                    (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, vm.location,
                                                                                       req.dst)
                    latency += pro_latency + trans_latency
                    data_base.req_trans_fee[req] += fee
                    data_base.store_latency(req, latency)
                continue
            # if no qualified vm or it's the first vnf, a new VM should be set up
            pro_latency = data_base.propagation_latency(placed_vms[req_vnfs[index - 1]].location, cand_dc)
            (tran_latency, trans_fee) = data_base.trans_latency_fee(req.data_size,
                                                                    placed_vms[req_vnfs[index - 1]], vm)
            # print("propagation latency from", placed_vms[req_vnfs[index - 1]].location, "to", vm.location, "is:",
            #       pro_latency)
            # print("transmission latency from", placed_vms[req_vnfs[index - 1]], "to", vm, "is:",
            #       tran_latency, ", fee is:", trans_fee)
            data_base.req_trans_fee[req] += trans_fee
            est_time[vnf_type] += pro_latency + tran_latency
            other_vnf_pro_times.append(pro_latency + tran_latency)
            cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
            # print("CPU_required: " + str(cpu_core))
            (process_t, start_t, new_vm) = data_base.start_new_vm(est_time[vnf_type], cpu_core, cand_dc, vnf_type,
                                                                  req.data_size)
            created_vms.append(new_vm)
            placed_vms[vnf_type] = [new_vm]
            # print("pro:", process_t, "start_t:", start_t)
            if index < len(req_vnfs) - 1:
                next_vnf = req_vnfs[index + 1]
                est_time[next_vnf] = start_t + process_t
                other_vnf_pro_times.append(process_t + start_t - est_time[vnf_type])
            elif index == len(req_vnfs) - 1:
                latency = start_t + process_t - req.arr_time
                # there are transmission latency and propagation latency from the last vm location to the dst node
                (trans_latency, pro_latency, fee) = data_base.internet_latency_fee(req.data_size, new_vm.location,
                                                                                   req.dst)
                latency += pro_latency + trans_latency
                data_base.req_trans_fee[req] += fee
                data_base.store_latency(req, latency)
        # index = 0
        else:
            (tran_latency, pro_latency, trans_fee) = data_base.internet_latency_fee(req.data_size,
                                                                                    req.src, cand_dc)
            # print("propagation latency from", req.src, "to", cand_dc, "is:", pro_latency)
            # print("transmission latency from", req.src, "to", cand_dc, "is:",
            #       tran_latency, ", fee is:", trans_fee)
            data_base.req_trans_fee[req] += trans_fee
            est_time[vnf_type] += pro_latency + tran_latency
            other_vnf_pro_times.append(pro_latency + tran_latency)
            cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
            # print("CPU_required: " + str(cpu_core))
            (process_t, start_t, new_vm) = data_base.start_new_vm(est_time[vnf_type], cpu_core, cand_dc, vnf_type,
                                                                  req.data_size)
            created_vms.append(new_vm)
            placed_vms[vnf_type] = new_vm


# Check if there is any qualified VM in the set to run a VNF
def check_vms_for_vnf(vms, vnf_type, est_time, req):
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
                install_time += service_chain.NetworkFunction(vnf_type).install_time
            process_time = req.data_size / (vm.cpu_cores * vnf_type.value[2])
            if est_time[vnf_type] + process_time + install_time < req.deadline - req.arr_time:
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

# This function is used to find the set of vms which are available at certain time slot,
# considering the processing latency of each VNF
# def get_qualified_vms(data_base, req):
