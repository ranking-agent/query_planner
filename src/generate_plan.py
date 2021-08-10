from .query_graph import convert_to_networkx
from .QueryPlan import QueryPlan, TerminalEvent

import networkx as nx
from collections import defaultdict

def generate_plan(trapi_query_graph):
    nxgraph = convert_to_networkx(trapi_query_graph)
    double_pins, components = decompose(nxgraph)
    plan = double_pins #these are already query plans
    for component in components:
        component_plan = generate_component_plan(component)
        plan.append(component_plan)
    return plan

def nodes_to_component( nodeset, master_graph, boundnodes ):
    """Given a set of nodes, find the induced subgraph that includes that list of nodes plus any
    adjacent boundnodes."""
    added_nodes = []
    for bn in boundnodes:
        for node in nodeset:
            if master_graph.has_edge(node,bn):
                nodeset.add(bn)
                break
    return master_graph.subgraph(nodeset).copy()

def get_bound_nodes(graph):
    #can this be replaced with the right nx incantation?
    bound_nodes = []
    nodes = graph.nodes(data = True)
    for node,nodedata in nodes:
        if nodedata['bound']:
            bound_nodes.append(node)
    return bound_nodes

def decompose(graph):
    """Given a graph that contains 1 or more bound nodes, find components that can be built entirely independently.
    If one part of a query graph is connected to another part only via a bound node, then the two parts are
    independent and the final answer is just a cartesian join across the two components."""
    #First handle the special case of single edges connecting 2 bound nodes.  The rest of the algorithm
    # chokes on that.
    clean_graph = graph.copy()
    direct_edges = []
    for u,v in graph.edges():
        if graph.nodes[u]['bound'] and graph.nodes[v]['bound']:
            direct_edges.append((u,v))
    double_pins = []
    for u,v in direct_edges:
        edge_id = graph.get_edge_data(u,v)['edge_id']
        plan = QueryPlan()
        plan.add_simple_dependency((frozenset(),frozenset()),edge_id)
        plan.add_simple_dependency(edge_id, TerminalEvent("double pin"))
        double_pins.append(plan)
        clean_graph.remove_edge(u,v)
    if clean_graph.number_of_edges() == 0:
        return double_pins,[]
    working_graph = clean_graph.copy()
    bound_nodes = get_bound_nodes(working_graph)
    working_graph.remove_nodes_from(bound_nodes)
    #having removed the bound nodes, do we have independent components?
    if nx.is_connected(working_graph):
        return double_pins , [clean_graph]
    node_components = nx.connected_components(working_graph)
    #Each component is a list of nodes.  We want to make them back into graphs, but we want them to include
    # the bound node where appropriate.
    components = [ nodes_to_component( nc, clean_graph, bound_nodes) for nc in node_components ]
    return double_pins, components

def generate_component_plan(component):
    hairs,bald_head = dehair(component)
    plan,traversed_graph = generate_simple_plan(bald_head)
    plan.add_hairs(hairs)
    return plan

def next_hair(component):
    for node,nd in component.nodes(data=True):
        if component.degree[node] == 1 and not nd['bound']:
            return node
    return None

#TODO: Maybe I need to build this one in a graph before moving it into a QueryPlan?
# The problem is that I'm building it by plucking off edges, but not in any partuclar order
#  therefore making it hard to track dependencies
def dehair(component):
    """The important thing about these hairs is that there are no constraints to apply.
    You can't do any better than starting at the bound end and walking forward."""
    #Hair is defined by degree 1 nodes.  As these are removed, more nodes become degree 1, so we backwalk
    # until it's all gone
    dangler = next_hair(component)
    dep_graph = defaultdict(list)
    while dangler is not None:
        cut_edge = list(component.edges(dangler,data=True))[0]
        edge_id =cut_edge[2]['edge_id']
        other_node = next(component.neighbors(dangler))
        dep_graph[other_node].append(cut_edge[2]['edge_id'])
        dep_graph[cut_edge[2]['edge_id']].append(dangler)
        component.remove_node(dangler)
        dangler = next_hair(component)
    #Because we went backwards, and because it was easier to keep track of, our depedency graph has nodes in it
    # but there's no event associated with these nodes; no joins are required.
    # So remove them from the dep graph to make the query plan
    tos = set(sum( list(dep_graph.values()), [] ))
    froms = set(dep_graph.keys())
    start_nodes = froms.difference(tos)
    #Get to the edges
    starts = set(sum( [dep_graph[n] for n in start_nodes], [] ))
    #The current dep_graph has both edges and nodes, but lets take out the nodes now
    plan = QueryPlan()
    for start in starts:
        plan.add_simple_dependency( (frozenset(), frozenset()), start )
    #The plan will have some terminal events as well, so that we have some dependency for the final edge.
    terminus = TerminalEvent('Hair')
    while len(starts) > 0:
        start = starts.pop()
        next_nodes = dep_graph[start]
        for node in next_nodes:
            if node not in dep_graph:
                plan.add_simple_dependency(start,terminus)
            else:
                for next_edge in dep_graph[node]:
                    plan.add_simple_dependency(start,next_edge)
                    starts.add(next_edge)
    return plan,component

def generate_simple_plan(g):
    """
    By this point, we have a single, bald, interdependent component.  It may have loops and/or branches, and
    will contain one or more bound nodes.

    The basic idea here is to find simple paths connecting bound nodes.   If this is a self binding, then we have
    a loop.   We will find those paths, and walk them from either end, joining in the middle.
    If we go in order from shortest to longest, then we are likely to apply constraints earlier.
    We also need to manage dependencies among the paths.

    This won't necessarily cover everything, (like hairs with loops at the end)
    so we need a bit of fail-safedness at the end"""
    #Stopping condition is when we have crossed all edges
    edge_count = g.number_of_edges()
    #First find all the simple paths and cycles
    paths = get_paths(g) + get_cycles(g)
    paths_with_length = [ (len(x),x) for x in paths ]
    paths_with_length.sort()
    #dep_graph = defaultdict(list)
    dep_graph = QueryPlan()
    traversed_subgraph = { 'nodes': set(), 'edges': set()}
    for l,path in paths_with_length:
        process_path(g, path, dep_graph, traversed_subgraph )
        if len(traversed_subgraph['edges']) == edge_count:
            break
    return dep_graph,traversed_subgraph

def process_path(graph,path,dep_graph,traversed_subgraph):
    """
    Given a path, generate the dependency graph
    :param graph:
    :param path:
    :param dep_graph:
    :return:  a tuple of a frozenset of nodes and a frozenset of edges.  This is the graph that has been run and
    filtered, and is also a key in the dep graph that the next path should use as its dependency
    """
    #First thing we need to do is to zing along the path until we get to a a part that we haven't previously traversed
    i = 0
    while graph.get_edge_data(path[i], path[i+1])['edge_id'] in traversed_subgraph['edges']:
        i += 1
    path = path[i:]
    i = -1
    while graph.get_edge_data(path[i], path[i-1])['edge_id'] in traversed_subgraph['edges']:
        i -= 1
    if i < -1:
        path = path[:i+1]
    #Now we have an actual path to traverse
    last = freeze_subgraph(traversed_subgraph)
    #update traversed subgraph for next time before we start whacking on path
    traversed_subgraph['nodes'].update(path)
    #Now add one from each end using the most recent join as the starting dependency
    startedge = dep_graph.add_dependency(graph, path[0], path[1], last, traversed_subgraph)
    endedge = dep_graph.add_dependency(graph, path[-1], path[-2], last, traversed_subgraph)
    path = path[1:-1]
    #Now add from each end using the node as the starting dependency
    while len(path) > 2:
        #Front
        startedge = dep_graph.add_dependency(graph,path[0],path[1],startedge,traversed_subgraph)
        #Back
        endedge = dep_graph.add_dependency(graph,path[-1],path[-2],endedge,traversed_subgraph)
        #cycle down
        path = path[1:-1]
    #Now path will either be 1 or 2 nodes long.
    if len(path) == 2:
        startedge = dep_graph.add_dependency(graph,path[1],path[0],startedge,traversed_subgraph)
    end = freeze_subgraph(traversed_subgraph)
    #Now add a join node.   This will also be used as the starting key for the next path
    dep_graph.add_simple_dependency(startedge, end)
    dep_graph.add_simple_dependency(endedge, end)

def freeze_subgraph(subgraph):
    return (frozenset(subgraph['nodes']), frozenset(subgraph['edges']))

def get_paths(g):
    bound_nodes = get_bound_nodes(g)
    paths = []
    for si,s in enumerate(bound_nodes):
        for t in bound_nodes[si+1:]:
            paths += nx.all_simple_paths(g,s,t)
    return paths

def get_cycles(g):
    bound_nodes = get_bound_nodes(g)
    cycles = nx.simple_cycles(g.to_directed())
    interim_cycles=[]
    for cycle in cycles:
        if len(cycle) < 3:
            continue
        for bn in bound_nodes:
            if bn in cycle:
                interim_cycles.append(format_cycle(cycle,bn))
                break
    #this gets us cycles in both directions.  We want to chuck that.
    uniquer = set()
    return_cycles = []
    for cycle in interim_cycles:
        s = frozenset(cycle)
        if s in uniquer:
            continue
        return_cycles.append(cycle)
        uniquer.add(s)
    return return_cycles

def format_cycle(cycle,bn):
    """
    I want the format of the cycles to be something like [A B C A] where A is the bound node.
    """
    loc = cycle.index(bn)
    return cycle[loc:] + cycle[:loc+1]
