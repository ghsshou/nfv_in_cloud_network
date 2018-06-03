import dijkstra


global_TS = 0.1  # The length of a time slot in ms


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


