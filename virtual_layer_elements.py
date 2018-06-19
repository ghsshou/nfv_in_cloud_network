from math import inf


class VirtualMachine(object):
    boot_time = 10  # Boot time of a VM, in time slot
    counter = 0

    # When start a new VM, assume that it is used to run a VNF. So, we should set the start time, use time. use time is
    # calculated according to the request.
    def __init__(self, start_time, use_time, cpu_cores, location):
        self.state = 'Active'  # Active or Closed
        self.start_time = start_time
        self.end_time = start_time + self.boot_time + use_time
        self.cpu_cores = cpu_cores
        self.vnfs = []  # [0] is always the one being running,
        # there are 2 vnfs at most, [1] denotes the one will run after [0]
        self.location = location
        self.available_time = self.end_time
        self.index = VirtualMachine.counter
        VirtualMachine.counter += 1

    def install_vnf(self, vnf):
        # print("enter install vnf function:", len(self.vnfs))
        # if len(self.vnfs) > 1:
        #     print("Error: Cannot add the VNF to this VM")
        #     return -1
        # print("XXXXX", len(self.vnfs))
        if self.state == 'Closed':
            return -1
        if len(self.vnfs) >= 1:
            # print("Now appending a VNF to the VM")
            # Next update the end time
            existed_flag = False
            # for val in self.vnfs:
            #     # print("XXXX:", val.name, vnf.name)
            #     if val.name == vnf.name:
            #         existed_flag = True
            #         break
            self.vnfs.append(vnf)
            # if not existed_flag:
                # print("XXXXSSSS")
            self.end_time = vnf.start_time + vnf.process_time + vnf.idle_length
            # if two vnfs are the same type, there is no need to install again
            # else:
            #     self.end_time = self.available_time + vnf.process_time + vnf.idle_length
            self.available_time = self.end_time - self.vnfs[-1].idle_length
            return 1
        if not self.vnfs:
            # print("Add a VNF")
            self.vnfs.append(vnf)
            self.available_time = self.end_time - self.vnfs[0].idle_length
            return 1

    # Return the next available time of VM
    def get_next_ava_time(self):
        return self.available_time

    # return whether a VNF is in a VM
    def host_vnf(self, vnf_type):
        for vnf in self.vnfs:
            if vnf_type.value[0] == vnf.name:
                return True
            else:
                return False

    # close the vm
    def close_vm(self):
        self.vnfs = []
        self.state = 'Closed'
        # print("[VM " + str(self.index) + " is closing, live time:"
        #       + str(self.start_time) + "--" + str(self.end_time) + "]")

    def __str__(self):
        # return "[VM " + str(self.index) + ", CPU core: " + str(self.cpu_cores) + \
        #     ", now running:" + self.vnfs[0].name + ", next available time:" + str(self.available_time) + \
        #        ", end time:" + str(self.end_time) + "]"
        return "[VM " + str(self.index) + ", CPU core: " + str(self.cpu_cores) + " start_time:" + str(self.start_time) + " end_time:" + str(self.end_time) + "]"

    def basic_info(self):
        return "VM:" + str(self.index) + ", CPU:" + str(self.cpu_cores) + ", len: " \
               + str(round(self.end_time - self.start_time, 2))
