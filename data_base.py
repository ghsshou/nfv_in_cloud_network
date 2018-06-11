import service_chain
import network_info
import traffic_generator
import virtual_layer_elements
import network_info as ni
import threading, time
from collections import defaultdict


class DataBase(object):
    rLock = threading.RLock()

    def __init__(self):
        self.vms = []  # Store the VM information in the network
        self.vnfs = []  # Store the instances of VMFs that are in the network
        self.scs = service_chain.ServiceChains()  # The service chains in the network
        self.network = network_info.NetworkInfo()
        self.tf_gen = None
        self.total_cpu_cost = 0
        self.latency = {}
        # self.basic_trans_capacity = 2  # Transmission capacity between VMs per CPU core in Gbps
        self.req_trans_fee = defaultdict(float)
        self.all_used_vm = []

    def add_service_chain(self, sc):
        self.scs.add_sc(sc)

    def add_vnf(self, vnf):
        if not isinstance(vnf, service_chain.NetworkFunction):
            print("Error: Input is not a VNF")
            return None
        self.vnfs.append(vnf)

    def rem_vnf(self, vnf):
        if not isinstance(vnf, service_chain.NetworkFunction):
            print("Error: Input is not a VNF")
            return None
        if vnf in self.vnfs:
            self.vnfs.remove(vnf)

    def add_datacenter(self, data_centers):
        self.network.add_data_center(data_centers)

    def set_traffic_generator(self, input_lambda, input_mu, max_req_num, optional_data_size=[]):
        self.tf_gen = traffic_generator.TrafficGenerator(input_lambda, input_mu, max_req_num, optional_data_size)
        # Para: service chain size, user node set, whether use optional data_size
        use_optional_size = 'continuous'
        if optional_data_size:
            use_optional_size = 'not_continuous'
        # print(use_optional_size)
        self.tf_gen.generate_traffic(self.scs.get_size(), self.network.get_user_nodes(), use_optional_size)

    # Get estimated start processing time of each vnf (according to basic processing capacity):
    @staticmethod
    def estimate_start_prc_time(start_time, data_size, vnf_type_sets):
        prc_time = {}
        processtime = start_time
        for vnf_type in vnf_type_sets:
            prc_time[vnf_type] = processtime
            processtime += int(data_size / vnf_type.value[2] / ni.global_TS)
        return prc_time

    # Start a VM with start time, and finish time, using a thread
    def start_new_vm(self, start_time, cpu, location, vnf_type, data_size):
        vnf = service_chain.NetworkFunction(vnf_type)
        use_time = self.estimate_vm_alive_length(vnf, data_size, cpu)
        processing_time = use_time - vnf.idle_length - vnf.install_time
        vm = self._start_new_vm(start_time, use_time, cpu, location)
        # print("XXXXXX", start_time, use_time)
        # print("Start a new VM:", vm)
        self.install_vnf_to_vm(vnf, processing_time, vm, start_time + vm.boot_time + vnf.install_time)
        # print(vm)
        # print("[VNF: " + str(vnf_type.value[0]) + ", VM: " + str(vm.index) + ", VNF processing time: " +
        #       str(processing_time) + ", Actually total use time:" + str(use_time) + "]")
        timer = threading.Timer((vm.end_time - start_time) * ni.global_TS, self._end_vm, args=(vm,))
        # timer = threading.Thread(target=self._end_vm, args=(vm,))
        # time.sleep((end_time - start_time) * ni.global_TS)
        timer.start()
        # t.join()
        # return an actual delay for the vnf, and the start process time for vnf
        return vnf.process_time, vnf.start_time, vm

    # Install a VNF to an existed VM
    def update_vm_w_vnf(self, vnf_type, vm, data_size, *start_time):
        vnf = service_chain.NetworkFunction(vnf_type)
        # if vm has already hosted such a VNF:
        if not vm.host_vnf(vnf_type):
            use_time = self.estimate_vm_alive_length(vnf, data_size, vm.cpu_cores)
            processing_time = use_time - vnf.idle_length - vnf.install_time
            start_process_vnf = vm.available_time
            self.install_vnf_to_vm(vnf, processing_time, vm, start_process_vnf + vnf.install_time)
        # return the value cost in the VNF, including processing time and install time
            return vnf.process_time, vnf.start_time
        # else, no need for installation
        else:
            use_time = self.estimate_vm_alive_length(vnf, data_size, vm.cpu_cores)
            use_time = use_time - vnf.install_time
            processing_time = use_time - vnf.idle_length
            start_process_vnf = vm.available_time
            self.install_vnf_to_vm(vnf, processing_time, vm, start_process_vnf)
            return vnf.process_time, vnf.start_time

    # Estimate the time a VM should keep alive, the result returned includes the processing time of a VNF
    # and its installation time and idle length, but not includes the boot time of a VM
    def estimate_vm_alive_length(self, vnf, data_size, cpu_cores):
        process_time = int(data_size / (vnf.throughput * cpu_cores) / ni.global_TS)  # Get how many TSs
        use_time = process_time + vnf.install_time + vnf.idle_length
        return use_time

    # Stop a VM after it finish tasks
    def _end_vm(self, vm):
        # self.rLock.acquire()
        if vm not in self.vms or vm.state == 'Closed':
            print("Remove Error: No such VM or VM is closed")
            return -1
        if len(vm.vnfs) == 1:
            vm.close_vm()
            self.total_cpu_cost += self.get_cost_of_vm(vm)
            self.vms.remove(vm)
            return 1
        # next_time is calculate complicate
        next_time = vm.vnfs[1].process_time + vm.vnfs[1].idle_length - \
                    (vm.vnfs[0].start_time + vm.vnfs[0].process_time +
                     vm.vnfs[0].idle_length - vm.vnfs[1].start_time)
        # print("pro", vm.vnfs[1].process_time, "start", vm.vnfs[1].start_time, "previous vm end time", vm.end_time)
        # if vm.end_time - vm.vnfs[1].start_time < 0:
        #     print("VM:", vm, "may have closed")
        vm.vnfs.pop(0)
        # print("VM still has task,next end time:", next_time)
        timer = threading.Timer(next_time * ni.global_TS, self._end_vm, args=(vm,))
        # t = threading.Thread(target=self._end_vm, args=(vm,))
        # time.sleep(next_time * ni.global_TS)
        timer.start()
        # self.rLock.release()
        # t.join()

    # Start a new VM
    def _start_new_vm(self, start_time, use_time, cpu, location):
        vm = virtual_layer_elements.VirtualMachine(start_time, use_time, cpu, location)
        self.vms.append(vm)
        self.all_used_vm.append(vm)
        return vm

    # Install a VNF to a VM
    def install_vnf_to_vm(self, vnf, processing_time, vm, start_time):
        if vm not in self.vms:
            print("**Error in fun. install_vnf_to_vm: no such VM")
            return -1
        vnf.set_processing_time(processing_time)  # Update the processing time of the instance
        vnf.set_start_time(start_time)  # Update the start processing time
        vm.install_vnf(vnf)

    # Get the set of VMs hosting the input VNF type
    def get_vms_w_vnf(self, vnf_type):
        # print("To find:", vnf_type.value[0])
        qualified_vms = []
        if not self.vms:
            return qualified_vms
        for vm in self.vms:
            if vm.host_vnf(vnf_type):
                qualified_vms.append(vm)
        return qualified_vms

    # Check whether the set of the VMs hosting a VNF is available in a certain Time Slot
    # Assuming the premise is that a VNF can become available only if it is now working
    # for a request or in an idle state
    def check_vms_at_time(self, vms, vnf_type, time_slot):
        if not vms:
            return None
        # print("XXXXX ", len(vms))
        to_remove = []
        for vm in vms:
            if not vm.host_vnf(vnf_type):
                to_remove.append(vm)
            else:
                if vm.get_next_ava_time() <= time_slot <= vm.end_time:
                    continue
                else:
                    # print("XXXXX remove")
                    to_remove.append(vm)
        if to_remove:
            for vm in to_remove:
                vms.remove(vm)

    # calculate the cost of a VM during its alive length
    def get_cost_of_vm(self, vm):
        live_length = vm.end_time - vm.start_time  # in second
        price = self.network.get_price_of_node(vm.location)
        return live_length * price * vm.cpu_cores / 3600  # the price is for per hour

    # Store the latency information for a request
    def store_latency(self, req, latency):
        if latency < req.deadline:
            self.latency[req] = latency
        else:
            self.latency[req] = -1

    # Average latency
    def average_latency(self):
        total = 0
        counter = 0
        for latency in self.latency.values():
            if latency != -1:
                total += latency
                counter += 1
        return total * ni.global_TS / counter

    # Blocking probability
    def blocking_probability(self):
        counter = 0
        for latency in self.latency.values():
            if latency == -1:
                counter += 1
        return counter / len(self.tf_gen.req_set)

    # Internet ingress/egress latency and fee
    def internet_latency_fee(self, data_size, src, dst):
        default_cap = ni.trans_cap  # Assuming the capacity is 10 Gbps
        trans_latency = int(data_size / default_cap / ni.global_TS)
        pro_latency = self.propagation_latency(src, dst)
        fee = ni.in_e_gress_fee * data_size
        return trans_latency, pro_latency, fee

    # Transmission fee and latency
    def trans_latency_fee(self, data_size, src_vm, dst_vm, capacity=-1):
        if capacity == -1:
            latency = int(data_size / (src_vm.cpu_cores * ni.basic_trans_capacity) / ni.global_TS)
        else:
            latency = int(data_size / capacity / ni.global_TS)
        if self.network.get_zone(src_vm.location) == self.network.get_zone(dst_vm.location):
            fee = 0
        else:
            fee = ni.trans_fee * data_size
        return latency, fee

    # Propagation latency
    def propagation_latency(self, src, dst):
        dis = self.network.get_shortest_dis(src, dst)
        return dis / ni.light_speed

    # Total cost
    def get_cost(self):
        while self.vms:
            # print("STILL HAVE!!")
            continue
        print("CPU cost ($):" + str(self.total_cpu_cost))
        trans_data_cost = sum(self.req_trans_fee.values())
        print("Data transmission cost ($):" + str(trans_data_cost))

    # All vm used
    def get_used_vm_no(self):
        print("Have used " + str(len(self.all_used_vm)) + " VMs in total")
        return len(self.all_used_vm)


