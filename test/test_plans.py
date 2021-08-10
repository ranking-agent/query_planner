import networkx as nx

from src.generate_plan import generate_plan
from src.QueryPlan import TerminalEvent

def construct_trapi(nodes,edges):
    trapi =  {"nodes": {}, "edges": {}}
    for node_id, bound in nodes.items():
        nv = {}
        if bound:
            nv={"ids":['']}
        trapi['nodes'][node_id] = nv
    for edge_id, (subject,object) in edges.items():
        trapi['edges'][edge_id] = {'subject': subject, 'object': object}
    return trapi

def test_one_hop():
    trapi = construct_trapi( {'n0':True, 'n1':False}, {'e0':('n0','n1')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.start() == ['e0']
    assert isinstance(plan.get_next('e0')[0], TerminalEvent)

def test_two_hop():
    trapi = construct_trapi({'n0': True, 'n1': False, 'n2': False}, {'e0': ('n0', 'n1'), 'e1': ('n1', 'n2')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.start() == ['e0']
    assert plan.get_next('e0') == ['e1']
    assert isinstance(plan.get_next('e1')[0], TerminalEvent)

def test_one_hop_two_bound():
    trapi = construct_trapi( {'n0':True, 'n1':True}, {'e0':('n0','n1')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.start() == ['e0']
    assert isinstance(plan.get_next('e0')[0], TerminalEvent)

def test_branch():
    """A Y pattern"""
    trapi = construct_trapi({'n0': True, 'n1': False, 'n2': False, 'n3': False}, {'e0': ('n0', 'n1'), 'e1': ('n1', 'n2'), 'e2': ('n1','n3')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.start() == ['e0']
    assert plan.get_next('e0') == ['e1','e2']
    assert isinstance(plan.get_next('e1')[0], TerminalEvent)
    assert isinstance(plan.get_next('e2')[0], TerminalEvent)

def test_branch_and_hair():
    """A Y pattern where two of the three terminal nodes are bound"""
    trapi = construct_trapi({'n0': True, 'n1': False, 'n2': True, 'n3': False},
                            {'e0': ('n0', 'n1'), 'e1': ('n1', 'n2'), 'e2': ('n1', 'n3')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.start() == ['e0','e1']
    join = (frozenset(['n0','n1','n2']),frozenset(['e0','e1']))
    assert plan.get_next('e0') == [join]
    assert plan.get_next('e1') == [join]
    assert plan.get_next(join) == ['e2']
    assert isinstance( plan.get_next('e2')[0] , TerminalEvent)

def test_double_branch():
    """A-B-C-D where A and D are bound, plus hair coming from B-E and C-F"""
    trapi = construct_trapi({'A': True, 'B': False, 'C': False, 'D': True, 'E': False, 'F': False},
                            {'AB': ('A', 'B'), 'BC': ('B', 'C'), 'CD': ('C', 'D'), 'BE': ('B','E'), 'CF': ('C','F')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.start() == ['AB', 'CD']
    #Note that a priori you don't know whether BC will be a dep of AB or CD, but this is the convention
    assert plan.get_next('AB') == ['BC']
    join = (frozenset(['A', 'B', 'C', 'D']), frozenset(['AB', 'BC', 'CD']))
    assert plan.get_next('BC') == plan.get_next('CD') == [join]
    assert frozenset(plan.get_next(join)) == frozenset(['BE', 'CF']) #wrapped in set to avoid order dependence
    assert isinstance(plan.get_next('BE')[0], TerminalEvent)
    assert isinstance(plan.get_next('CF')[0], TerminalEvent)

def test_hairy_loop():
    """A-B-C-D-A-E: A diamond where  B is bound, and there's a hair (E) hanging off one vertex"""
    trapi = construct_trapi({'A': False, 'B': True, 'C': False, 'D': False, 'E': False},
                            {'AB': ('A', 'B'), 'BC': ('B', 'C'), 'CD': ('C', 'D'), 'DA': ('D','A'), 'AE': ('A','E')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert set(plan.start()) == set(['AB', 'BC'])
    # Note that a priori you don't know whether BC will be a dep of AB or CD, but this is the convention
    assert plan.get_next('AB') == ['DA']
    assert plan.get_next('BC') == ['CD']
    join = (frozenset(['A', 'B', 'C', 'D']), frozenset(['AB', 'BC', 'CD','DA']))
    assert plan.get_next('DA') == plan.get_next('CD') == [join]
    assert plan.get_next(join) == ['AE']
    assert isinstance(plan.get_next('AE')[0], TerminalEvent)

def test_two_component_one_hops():
    """A-B-C where B is bound.  Is two independent onehops from B"""
    trapi = construct_trapi({'A': False, 'B': True, 'C': False},
                            {'AB': ('A', 'B'), 'BC': ('B', 'C')})
    plans = generate_plan(trapi)
    assert len(plans) == 2
    start0 = plans[0].start()
    start1 = plans[1].start()
    assert len(start0) == len(start1) == 1
    assert set(start0 + start1) == set( ['AB', 'BC'])

def test_double_loop():
    """A-B-C-D-A, and B-D.  It's a diamond with a crossbar.  The bound node is one of the degree 2 vertices (A)"""
    trapi = construct_trapi({'A': True, 'B': False, 'C': False, 'D': False},
                            {'AB': ('A', 'B'), 'BC': ('B', 'C'), 'CD': ('C', 'D'), 'DA': ('D','A'), 'BD': ('B','D')})
    plans = generate_plan(trapi)
    assert len(plans) == 1
    plan = plans[0]
    assert set(plan.start()) == set(['AB','DA'])
    #Do the smallest loop first
    # One of AB, DA will have 'BD' as a child, while the other will have the join
    assert plan.get_next('DA') == ['BD']
    next_plans = set(plan.get_next('DA') + plan.get_next('AB'))
    join = (frozenset(['A','B','D']), frozenset(['AB','BD','DA']))
    assert next_plans ==set([join,'BD'])
    assert plan.get_next('BD') == [join]
    assert set(plan.get_next(join)) == set(['BC','CD'])
    join2 = (frozenset(['A','B','D','C']), frozenset(['AB','BD','DA','BC','CD']))
    assert plan.get_next('CD') == [join2]
    assert plan.get_next('BC') == [join2]

def test_readme():
    """Planning the query shown in README.md"""
    trapi = construct_trapi({'A': True, 'B': True, 'C': False, 'D': False, 'E':False, 'F': False,
                             'G': False, 'H': False, 'I':True},
                            {'AB': ('A', 'B'), 'BC': ('B', 'C'), 'AC': ('A', 'C'), 'CD': ('C', 'D'),
                             'DE': ('D','E'), 'DF': ('D','F'), 'EF': ('E','F'), 'FG': ('F', 'G'),
                             'GH': ('G','H'), 'GI':('G','I')})
    plans = generate_plan(trapi)
    assert len(plans) == 2
    plan = plans[0]
    assert plan.start() == ['AB']
    planb = plans[1]
    assert set(planb.start()) == set(['AC','BC'])
    join1 = ( frozenset(['A','B','C']), frozenset(['AC','BC']))
    assert planb.get_next('AC') == planb.get_next('BC') == [join1]
    assert set(planb.get_prev(join1)) == set( [ 'AC', 'BC'])
    assert set(planb.get_next(join1)) == set(['CD','GI'])
    assert planb.get_next('CD') == ['DF']
    assert planb.get_next('GI') == ['FG']
    join2 = ( frozenset(['A','B','C','D','F','G','I']), frozenset(['AC','BC','CD','DF','FG','GI']))
    assert planb.get_next('DF') == planb.get_next('FG') == [join2]
    assert set(planb.get_next(join2)) == set(['DE','EF'])
    join3 = ( frozenset(['A','B','C','D','E','F','G','I']), frozenset(['AC','BC','CD','DF','FG','GI','DE','EF']))
    assert planb.get_next('DE') == planb.get_next('EF') == [join3]
    assert planb.get_next(join3) == ['GH']
    assert isinstance(planb.get_next('GH')[0], TerminalEvent)

