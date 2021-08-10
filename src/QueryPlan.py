from collections import defaultdict

class QueryPlan:
    def __init__(self):
        self.nexts = defaultdict(list)
        self.prevs = defaultdict(list)
    def add_dependency(self, graph, fromnode, tonode, last, traversed_subgraph):
        edge_id = graph.get_edge_data(fromnode, tonode)['edge_id']
        self.nexts[last].append(edge_id)
        self.prevs[edge_id].append(last)
        traversed_subgraph['edges'].add(edge_id)
        return edge_id
    def add_simple_dependency(self, upstream, joinnode):
        self.nexts[upstream].append(joinnode)
        self.prevs[joinnode].append(upstream)
    def start(self):
        emptygraph = (frozenset(), frozenset())
        return self.get_next(emptygraph)
    def end(self):
        downstreams = set(self.prevs.keys())
        upstreams = set(self.nexts.keys())
        ends = list( downstreams.difference(upstreams))
        return ends
    def get_next(self,x):
        if x in self.nexts:
            return self.nexts[x]
        elif x in self.prevs:
            return []
        else:
            return TerminalEvent(f'{x} has no next')
    def get_prev(self, x):
        if x in self.prevs:
            return self.prevs[x]
        else:
            return (frozenset(),frozenset())
    def add_component_plan(self,x):
        pass
    def add_hairs(self,hair_graph):
        if len(hair_graph.nexts) == 0:
            return
        if len(self.nexts) == 0:
            self.nexts = hair_graph.nexts
            self.prevs = hair_graph.prevs
            return
        ends = self.end()
        hair_starts = hair_graph.start()
        del hair_graph.nexts[(frozenset(),frozenset())]
        self.nexts.update(hair_graph.nexts)
        self.prevs.update(hair_graph.prevs)
        for end in ends:
            self.nexts[end].extend(hair_starts)
        for start in hair_starts:
            self.prevs[start].extend(ends)

class TerminalEvent:
    def __init__(self,name):
        self.name = name