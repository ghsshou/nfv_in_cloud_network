import dijkstra
from enum import Enum, unique


global_TS = 0.1  # The length of a time slot in s
trans_fee = 0.01  # Price of data transferred between VMs in different zones, in Gb
light_speed = 200000  # km/s


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
        self._graph.shortest_path(src, dst)



@unique
class CPUPrice(Enum):
    z1 = ['0', 0.033174]  # name, price (per CPU per hour)
    z2 = ['1', 0.043174]
    z3 = ['2', 0.023174]


