import service_chain
import network_info
import traffic_generator
import virtual_layer_elements
import network_info as ni
import threading


class DataBase(object):

    def __init__(self):
        self.vms = []  # Store the VM information in the network
        self.vnfs = []  # Store the instances of VMFs that are in the network
        self.scs = service_chain.ServiceChains()  # The service chains in the network
        self.network = network_info.NetworkInfo()
        self.tf_gen = None

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


    # Start a new VM
    def start_new_vm(self, start_time, cpu, location):
        vm = virtual_layer_elements.VirtualMachine(start_time, cpu, location)
        self.vms.append(vm)
        return vm

    # Install a VNF to a VM
    def install_vnf_to_vm(self, vnf_type, vm, data_size):
        vnf = service_chain.NetworkFunction(vnf_type)
        process_time = None
        if vm not in self.vms:
            print("Error: VM")
        if vnf.thread_attr == 1:
            process_time = int(data_size / (vnf.throughput * vm.cpu_cores) / ni.global_TS)  # Get how many TSs will
            # consume for the data
        else:
            process_time = int(data_size / vnf.throughput / ni.global_TS)
        vnf.set_finish_time(process_time)  # Update the finish time of the instance
        if vm in self.vms:
            vm.install_vnf(vnf)
        else:
            print("This is not such VM")

    # Get the set of instances of VNFs in the network
    # The input parameter is the VNF name
    def get_instances_of_vnf(self, vnf_type):
        # print("Input:", vnf_type.name)
        if vnf_type not in service_chain.NetworkFunctionName:
            print("Error: No such VNF type")
            return None
        results = []
        for vnf in self.vnfs:
            # print("!!!VNF", vnf)
            if vnf.name == vnf_type.value[0]:
                results.append(vnf)
                # print("Find:", vnf)
        return results

    # Get the set of VMs hosting the input VNF type
    def get_vms_w_vnf(self, vnf_type):
        print("To find:", vnf_type.value[0])
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
        for vm in vms:
            if not vm.host_vnf(vnf_type):
                vms.remove(vm)
            else:
                if vm.get_next_ava_time() <= time_slot:
                    continue
                else:
                    vms.remove(vm)
