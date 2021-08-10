import networkx as nx

def convert_to_networkx(query_graph):
    """Convert a TRAPI query graph into a networkx graph."""
    graph = nx.Graph()
    for node,node_props in query_graph['nodes'].items():
        graph.add_node(node,bound='ids' in node_props)
    for edge,edge_props in query_graph['edges'].items():
        graph.add_edge(edge_props['subject'],edge_props['object'],edge_id=edge)
    return graph
