from src.query_graph import convert_to_networkx

def test_simple():
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
    assert len(nxg.nodes) == 2
    assert len(nxg.edges) == 1
    assert nxg.nodes['n02']['bound']
    assert not nxg.nodes['n01']['bound']