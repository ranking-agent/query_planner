import networkx as nx

from src.query_graph import convert_to_networkx
from src.generate_plan import decompose

def test_onehop():
    query_graph = {
        "nodes": {
            "n01":
                {
                   "categories":['biolink:X']
                },
            "n02":
                {
                    "ids": ["NC:7"]
                }
        },
        "edges": {
            "e1":
                {
                    "subject": "n01",
                    "object": "n02",
                    "predicates": ["biolink:predicate"]
                }
        }
    }
    nxg = convert_to_networkx(query_graph)
    _, components = decompose(nxg)
    assert len(components) == 1
    assert len(_) == 0
    assert nx.is_isomorphic(components[0], nxg) #not equal b/c we do some copying in the guts

def test_simple_from_nx():
    """TRAPI too verbose"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    _,components = decompose(g)
    assert len(components) == 1

def test_two_component():
    """A 2-hop with a bound in the middle should be run as 2 independent onehops"""
    g = nx.Graph()
    g.add_node('n0',bound=False)
    g.add_node('n1',bound=True)
    g.add_node('n2',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_edge('n2','n1',edge_id='e2')
    _,components = decompose(g)
    assert len(components) == 2
    for cg in components:
        assert len(cg.nodes) == 2
        assert len(cg.edges) == 1
        assert 'n1' in cg

def test_loop():
    """A one hop from a bound and an independent loop from the bound should be separated.
    Checks the case in which one component has multiple edges to the same bound node"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_node('n2',bound=False)
    g.add_node('n3',bound=False)
    g.add_edge('n0','n1',edge_id='e1')
    g.add_edge('n2','n1',edge_id='e2')
    g.add_edge('n0','n2',edge_id='e3')
    g.add_edge('n0','n3',edge_id='e4')
    _,components = decompose(g)
    assert len(components) == 2
    found_little = found_big = False
    for cg in components:
        if len(cg.nodes) == 2:
            found_little=True
            assert len(cg.edges('n0')) == 1
        elif len(cg.nodes) == 3:
            found_big = True
            assert len(cg.edges('n0')) == 2
        else:
            assert False
    assert found_little and found_big

def test_two_bound():
    g = nx.Graph()
    g.add_node('n0', bound=False)
    g.add_node('n1', bound=True)
    g.add_edge('n0', 'n1', edge_id='e1')
    g.add_node('n2', bound=False)
    g.add_edge('n1', 'n2', edge_id='e2')
    g.add_node('n3', bound=True)
    g.add_edge('n2', 'n3', edge_id='e2')
    g.add_node('n4', bound=False)
    g.add_edge('n3', 'n4', edge_id='e3')
    _,components = decompose(g)
    assert len(components) == 3
    found_n1 = False
    found_n3 = False
    found_big = False
    for gc in components:
        if len(gc.nodes) == 3:
            assert 'n1' in gc
            assert 'n3' in gc
            assert len(gc.edges) == 2
            found_big = True
        else:
            assert len(gc.nodes) == 2
            assert len(gc.edges) == 1
            if 'n1' in gc:
                found_n1 = True
            elif 'n3' in gc:
                found_n3 = True
    assert found_n1 and found_n3 and found_big

