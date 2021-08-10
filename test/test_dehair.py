import networkx as nx
from src.generate_plan import dehair
from src.QueryPlan import TerminalEvent

def test_short_path():
    """The normal n-hop from a single bound node"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    dep_graph,components = dehair(g)
    assert len(components.nodes) == 1
    assert dep_graph.start() == ['e1']
    assert isinstance( dep_graph.get_next('e1')[0] , TerminalEvent)

def test_simple_path():
    """The normal n-hop from a single bound node"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_node('n2',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_edge('n1','n2',edge_id='e2')
    dep_graph,components = dehair(g)
    assert len(components.nodes) == 1
    assert 'n0' in components
    assert dep_graph.start() == ['e1']
    assert dep_graph.get_next('e1') == ['e2']
    assert isinstance( dep_graph.get_next('e2')[0] , TerminalEvent)

def test_branch():
    """A branch is really must more hair"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_node('n2',bound=False)
    g.add_edge('n1','n2',edge_id='e2')
    g.add_node('n3',bound=False)
    g.add_edge('n1','n3',edge_id='e3')
    dep_graph,components = dehair(g)
    assert len(components.nodes) == 1
    assert 'n0' in components
    assert dep_graph.start() == ['e1']
    assert dep_graph.get_next('e1') == ['e2','e3']
    assert isinstance(dep_graph.get_next('e2')[0], TerminalEvent)
    assert isinstance(dep_graph.get_next('e3')[0], TerminalEvent)

def test_dangler():
    """A-B-C, B-D where A,C are bound"""
    g = nx.Graph()
    g.add_node('A',bound=True)
    g.add_node('B',bound=False)
    g.add_edge('A','B',edge_id='e1')
    g.add_node('C',bound=True)
    g.add_edge('B','C',edge_id='e2')
    g.add_node('D',bound=False)
    g.add_edge('B','D',edge_id='x')
    dep_graph,components = dehair(g)
    assert len(components.nodes) == 3
    assert dep_graph.start() == ['x']
    assert isinstance(dep_graph.get_next('x')[0], TerminalEvent)
