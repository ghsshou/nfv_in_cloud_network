import dijkstra
from enum import Enum, unique


global_TS = 0.1  # The length of a time slot in s
trans_fee = 0.01  # Price of data transferred between VMs in different zones, in Gb
light_speed = 20000000  # km/s
in_e_gress_fee = 0.01  # the fee of traffic ingress and egress Internet (per GB)
trans_cap = 1000  # Ingress and egress transmission capacity
basic_trans_capacity = 100  # Transmission capacity between VMs per CPU core in Gbps


class NetworkInfo(object):
    _path = "COST239"

    def __init__(self, *data_centers):
        self._graph = dijkstra.Graph()
        self._graph.read_from_file(NetworkInfo._path)
        self._data_centers = set(data_centers)
        self._user_nodes = self._graph.nodes - self._data_centers

    def add_data_center(self, data_center):
        self._data_centers.update(data_center)
        self._user_nodes = self._user_nodes - self._data_centers

    def get_data_centers(self):
        return self._data_centers

    def get_user_nodes(self):
        return self._user_nodes

    def get_price_of_node(self, node):
        zone = self._graph.zones[node]
        for price in CPUPrice:
            if zone == price.value[0]:
                return price.value[1]

    def get_zone(self, node):
        return self._graph.zones[node]

    def get_shortest_dis(self, src, dst):
        result = self._graph.shortest_path(src, dst)
        return result[1]

    def find_nearest_zone(self, node):
        shorest_dis = float('inf')
        nearest_dc = None
        for data_center in self._data_centers:
            if self.get_shortest_dis(node, data_center) < shorest_dis:
                nearest_dc = data_center
                shorest_dis = self.get_shortest_dis(node, data_center)
        zone = None
        if nearest_dc:
            zone = self.get_zone(nearest_dc)
        return zone, nearest_dc


@unique
class CPUPrice(Enum):
    z1 = ['0', 0.033174]  # name, price (per CPU per hour)
    z2 = ['1', 0.043174]
    z3 = ['2', 0.023174]


if __name__ == "__main__":
    network = NetworkInfo("0", "10")
    zone = network.find_nearest_zone("11")
    print(zone)
