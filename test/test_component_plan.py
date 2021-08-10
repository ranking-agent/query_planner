import networkx as nx

from src.generate_plan import generate_component_plan
from src.QueryPlan import TerminalEvent

def test_branched_component_plan():
    """Component plan should add hair"""
    g = nx.Graph()
    g.add_node('n0',bound=True)
    g.add_node('n1',bound=False)
    g.add_node('n2',bound=True)
    g.add_node('n3',bound=False)
    g.add_edge('n0','n1',edge_id='e0')
    g.add_edge('n2','n1',edge_id='e2')
    g.add_edge('n3','n1',edge_id='e3')
    p = generate_component_plan(g)
    assert p.start() == ['e0','e2']
    join = (frozenset(['n0', 'n1', 'n2']), frozenset(['e0', 'e2']))
    assert p.get_next('e0') == p.get_next('e2') == [join]
    assert p.get_next(join) == ['e3']
    assert isinstance( p.get_next('e3')[0], TerminalEvent)

