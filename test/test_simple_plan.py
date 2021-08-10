import networkx as nx
from collections import defaultdict
from src.QueryPlan import QueryPlan

from src.generate_plan import generate_simple_plan, get_paths, get_cycles, process_path

def test_paths():
    """One path going n0*-n1-n2-n3*.  Also n1-n4-n2."""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_node('n3',bound=True)
    g.add_edge('n2','n3',edge_id='e3')
    g.add_node('n4',bound=False)
    g.add_edge('n1','n4',edge_id='x1')
    g.add_edge('n2','n4',edge_id='x2')
    paths = get_paths(g)
    assert len(paths) == 2
    cycles = get_cycles(g)
    assert len(cycles) == 0

def test_cycle():
    """This one is a triangle, with one bound vertex"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_edge('n2','n0',edge_id='e3')
    paths = get_paths(g)
    assert len(paths) == 0
    cycles = get_cycles(g)
    assert len(cycles) == 1
    cycle = cycles[0]
    assert cycle[0] == 'n0'
    assert cycle[-1] == 'n0'
    assert len(cycle) == 4

def test_generate():
    """One path going n0*-n1-n2-n3*.  Also n1-n4-n2."""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_node('n3',bound=True)
    g.add_edge('n2','n3',edge_id='e3')
    g.add_node('n4',bound=False)
    g.add_edge('n1','n4',edge_id='x1')
    g.add_edge('n2','n4',edge_id='x2')
    generate_simple_plan(g)

def test_process_even_path():
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_node('n3',bound=True)
    g.add_edge('n2','n3',edge_id='e3')
    dep = QueryPlan()
    traversed_subgraph = {'nodes': set(), 'edges': set()}
    frozen = (frozenset() ,frozenset())
    process_path(g,['n0','n1','n2','n3'],dep,traversed_subgraph)
    assert dep.start() == ['e1','e3']
    assert dep.get_next('e1') == ['e2']
    final = (frozenset(['n0','n1','n2','n3']), frozenset(['e1','e2','e3']))
    assert dep.get_next('e2') == [final]
    assert dep.get_next('e3') == [final]

def test_process_odd_cycle():
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_node('n3',bound=False)
    g.add_edge('n2','n3',edge_id='e3')
    g.add_edge('n0','n3',edge_id='e4')
    dep = QueryPlan()
    traversed_subgraph = {'nodes': set(), 'edges': set()}
    process_path(g,['n0','n1','n2','n3','n0'],dep,traversed_subgraph)
    assert dep.start() == ['e1','e4']
    assert dep.get_next('e1') == ['e2']
    assert dep.get_next('e4') == ['e3']
    final = (frozenset(['n0','n1','n2','n3']), frozenset(['e1','e2','e3','e4']))
    assert dep.get_next('e2') == [final]
    assert dep.get_next('e3') == [final]

def test_plan():
    """One path going n0*-n1-n2-n3*.  Also n1-n4-n2."""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_node('n3',bound=True)
    g.add_edge('n2','n3',edge_id='e3')
    g.add_node('n4',bound=False)
    g.add_edge('n1','n4',edge_id='x1')
    g.add_edge('n2','n4',edge_id='x2')
    plan,_ = generate_simple_plan(g)
    assert plan.start() == ['e1','e3']
    assert plan.get_next('e1') == ['e2']
    join1 = (frozenset(['n0','n1','n2','n3']), frozenset(['e1','e2','e3']))
    assert plan.get_next('e3') == [join1]
    assert plan.get_next('e2') == [join1]
    assert plan.get_next(join1) == ['x1','x2']
    join2= (frozenset(['n0','n1','n2','n3','n4']), frozenset(['e1','e2','e3','x1','x2']))
    assert plan.get_next('x1') == [join2]
    assert plan.get_next('x2') == [join2]
    assert plan.get_next(join2) == []
    assert plan.end() == [join2]