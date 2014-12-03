class Graph:
    def __init__(self):
        self.graph = {}

        # edges contain edge_id: [nodes connected to it]
        self.edges = {}
        self.nodes = []
    
    def add_node(self, node, edges):
        for e in edges:
            if self.edges.has_key(e):
                # check if node is joined to e
                if not node in self.edges[e]:
                    self.edges[e].append(node)
            else:
                self.edges[e] = [node]

        if not node in self.nodes:
            self.nodes.append(node)
            self.graph[node] = []
            for e in edges:
                for neighbor in self.edges[e]:
                    if neighbor != node:
                        if neighbor not in self.graph[node]:
                            self.graph[node].append(neighbor)
                        if node not in self.graph[neighbor]:
                            self.graph[neighbor].append(node)

    def remove_node(self, node):
        self.nodes.remove(node)
        del self.graph[node]

        for e in self.edges:
            if node in self.edges[e]:
                self.edges[e].remove(node)

        for n in self.graph:
            if node in self.graph[n]:
                self.graph[n].remove(node)

    def shortest_path_hop_to_edge(self, src, edge):
        shortest = 2000
        chosen_node = None
        chosen_path = None
        for n in self.edges[edge]:
            candidate = self.shortest_path(src,n)
            if candidate == None:
                chosen_path = ['--']
            else:
                if len(candidate) <= shortest:
                    shortest = len(candidate)
                    chosen_node = n
                    chosen_path = candidate

        if len(chosen_path) == 1:
            return chosen_path[0]
        else:
            return chosen_path[1]

    def routing_table(self, node):
        table = {}
        for e in self.edges:
            table[e] = self.shortest_path_hop_to_edge(node, e)

        return table

    def shortest_path(self, src, dst, path = []):
        path = path + [src]
        if src == dst:
            return path
        if not self.graph.has_key(src):
            return None
        shortest = None

        for node in self.graph[src]:
            if node not in path:
                newpath = self.shortest_path(node, dst, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath

        return shortest

    def connected(self, src, dst):
        # dumb implementation, 
        # just check if there is a shortest path
        if self.shortest_path(src,dst) != None:
            return True
        else:
            return False

    def print_graph(self):
        #print self.nodes
        #print self.edges
        print self.graph

if __name__ == "__main__":
    g = Graph()
    g.add_node('01',['01','02'])
    g.print_graph()
    print "\n"
    g.add_node('02',['01','02'])
    g.print_graph()
    print "\n"
    g.add_node('03',['02','04','05'])
    g.print_graph()
    print "\n"
    g.add_node('04',['04','03','05'])
    g.print_graph()
    print "\n"
    g.add_node('05',['06','05'])

    g.print_graph()

    #print g.shortest_path('01','05')

    #g.remove_node('04')

    #print g.shortest_path('01','05')
