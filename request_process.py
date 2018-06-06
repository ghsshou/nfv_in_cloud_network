import threading
import network_info as ni
import math

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
            temp = data_base.update_vm_w_vnf(vnf_type, vms[0], req.data_size)
            other_vnf_pro_times.append(temp)

        else:
            cpu_core = cal_cpu_cores(vnf_type, req.data_size, req.deadline, other_vnf_pro_times)
            print("CPU_required: " + str(cpu_core))
            temp = data_base.start_new_vm(est_time[vnf_type], cpu_core, '0', vnf_type, req.data_size)
            other_vnf_pro_times.append(temp)
            # data_base.install_vnf_to_vm(vnf_type, new_vm, req.data_size)
            # print(new_vm)
            # shut_down_vm_after(data_base, new_vm, 20)


# # End a VM after a period, t is Time Slot
# def shut_down_vm_after(data_base, vm, t):
#     if vm not in data_base.vms:
#         print("Error: no such VM")
#         return None
#     timer = threading.Timer(t * ni.global_TS, _shut_down_vm, args=(data_base, vm))
#     timer.start()
#
#
# # Shutdown a VM
# def _shut_down_vm(data_base, vm):
#     print("Now close VM:" + str(vm.index) + ",Start at:" + str(vm.start_time))
#     vm.close_vm()
#     data_base.vms.remove(vm)

# Estimate time using Eqn. 1
def cal_cpu_cores(vnf_type, data_size, ddl, other_vnf_pro_times):
    if vnf_type.value[1] == 0:
        return 1
    max_time = ddl - sum(other_vnf_pro_times)
    return math.ceil(data_size / vnf_type.value[2] / (max_time * ni.global_TS) )






# This function is used to find the set of vms which are available at certain time slot,
# considering the processing latency of each VNF
# def get_qualified_vms(data_base, req):


