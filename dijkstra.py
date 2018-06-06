from collections import defaultdict
from math import inf


class Graph(object):
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(list)
        self.distance = {}
        self.zones = {}

    def add_edge(self, src, dst, dist, direction='bidirectional'):
        self.nodes.add(src)
        self.nodes.add(dst)
        if direction == 'bidirectional':
            self.edges[src].append(dst)
            self.distance[(src, dst)] = dist
            self.edges[dst].append(src)
            self.distance[(dst, src)] = dist

    def read_from_file(self, path):
        with open(path, 'r') as f:
            for line in f.readlines():
                if line.strip()[0] != '#':
                    content = line.split()
                    # read source node, destination node, and distance
                    src = content[0]
                    dst = content[1]
                    dist = int(content[2])
                    if len(content) == 4:
                        self.zones[src] = content[3]
                    self.add_edge(src, dst, dist)

    def shortest_paths(self, src):
        not_visited_nodes = set(self.nodes)
        pre_node = {}
        short_dist = {src: 0}
        # initialize
        for node in not_visited_nodes:
            if (src, node) in self.distance.keys():
                short_dist[node] = self.distance[(src, node)]
                pre_node[node] = src
            else:
                short_dist[node] = inf
        not_visited_nodes.remove(src)
        while not_visited_nodes:
            # find the candidate node with the shortest edge in this loop
            candidate = None
            min = inf
            for node in not_visited_nodes:
                if short_dist[node] < min:
                    candidate = node
                    min = short_dist[node]
            # print('shortest node:' + candidate + ":", min)
            # update the info with the new candidate node
            for end_node in not_visited_nodes:
                if (candidate, end_node) in self.distance.keys():
                    if short_dist[end_node] > self.distance[(candidate, end_node)] + short_dist[candidate]:
                        pre_node[end_node] = candidate
                        short_dist[end_node] = self.distance[(candidate, end_node)] + short_dist[candidate]
            not_visited_nodes.remove(candidate)
        # delete the source node
        short_dist.pop(src)
        short_path = defaultdict(list)
        for node in (self.nodes - set(src)):
            short_path[node].append(node)
            v = node
            # print("now:" + v)
            while pre_node[v] != src:
                short_path[node].insert(0, pre_node[v])
                v = pre_node[v]
        return short_path, short_dist

    def shortest_path(self, src, dst):
        paths = self.shortest_paths(src)
        path = paths[0][dst]
        dis = paths[1][dst]
        return path, dis

    def print_topology(self):
        print("Node Number: %d" % len(self.nodes))
        for ((src, dst), dist) in self.distance.items():
            print("[" + src + "-->" + dst + ": " + str(dist) + "]")

    # print the path info, path is in form of a node list, not including the source node
    @staticmethod
    def print_path(src, path):
        print("[" + src + "->" + path[-1] + ": " + src +"->", end="")
        for node in path[:-1]:
            print(node + "->", end="")
        print(path[-1] + "]")


if __name__ == "__main__":
    graph = Graph()
    graph.read_from_file('COST239')
    # graph.print_topology()
    src = "0"
    dst = "11"
    # paths = graph.shortest_paths(src)
    # for path in paths[0].values():
    #     graph.print_path(src, path)
    #     print("Distance:", paths[1][path[-1]])
    path = graph.shortest_path(src, dst)
    graph.print_path(src, path[0])

