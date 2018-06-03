
def process_one_req(data_base, req):
    req_vnfs = list(data_base.scs.get_sc(req.sc))  # Get the name of vnfs
    vm_w_vnf = {}
    est_time = data_base.estimate_start_prc_time(req.arr_time, req.data_size, data_base.scs.get_sc(req.sc))
    for vnf_type in req_vnfs:
        print("Estimated start processing time", est_time[vnf_type])
        # vnf = data_base.get_instances_of_vnf(vnf_type)
        # print(vnf)
        vms = data_base.get_vms_w_vnf(vnf_type)
        data_base.check_vms_at_time(vms, vnf_type, est_time[vnf_type])
        if vms:
            vm_w_vnf[vnf_type] = vms
            print(vms[0])
        else:
            new_vm = data_base.start_new_vm(est_time[vnf_type], 1, '0')
            data_base.install_vnf_to_vm(vnf_type, new_vm, req.data_size)
            print(new_vm)



# This function is used to find the set of vms which are available at certain time slot,
# considering the processing latency of each VNF
# def get_qualified_vms(data_base, req):


