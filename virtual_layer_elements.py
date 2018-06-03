from math import inf


class VirtualMachine(object):
    boot_time = 5  # Boot time of a VM, in time slot
    counter = 0

    def __init__(self, start_time, cpu_cores, location):
        self.state = 'Active'  # Active or Closed
        self.start_time = start_time
        self.cpu_cores = cpu_cores
        self.vnfs = []  # [0] is always the one being running,
        # there are 2 vnfs at most, [1] denotes the one will run after [0]
        self.location = location
        self.index = VirtualMachine.counter
        VirtualMachine.counter += 1

    def install_vnf(self, vnf):
        if len(self.vnfs) > 1:
            print("Error: Cannot add the VNF to this VM")
        self.vnfs.append(vnf)

    # Return the next available time of VM
    def get_next_ava_time(self):
        if len(self.vnfs) > 1:
            return inf
        return self.vnfs[0].finish_time

    # return whether a VNF is working now in a VM
    def host_vnf(self, vnf_type):
        for vnf in self.vnfs:
            if vnf_type.value[0] == vnf.name:
                return True
            else:
                return False

    # close the vm
    def close_vm(self):
        self.state = 'Closed'

    def __str__(self):
        return "[VM " + str(self.index) + ", CPU core: " + str(self.cpu_cores) + \
            ", now running:" + self.vnfs[0].name + ", next available time:" + str(self.get_next_ava_time()) + "]"