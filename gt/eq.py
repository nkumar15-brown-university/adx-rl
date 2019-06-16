from typing import List, Dict, Tuple

import networkx as nx


# The following are a few different aggregation functions
def inner_max(l):
    return [max(x) for x in l]


def inner_min(l):
    return [min(x) for x in l]


def inner_mean(l):
    return [sum(x) / float(len(x)) for x in l]


def outer_mean(l):
    return sum(l) / float(len(l))


aggregators = {  # "max-max": (max, inner_max),
    "min-min": (min, inner_min),
    # "min-avg":(min, inner_mean),
    # "max-avg":(max, inner_mean),
    # "avg-min": (outer_mean, inner_min),
    # "avg-avg": (outer_mean, inner_mean)#
}


def aggregate(revenue_per_node_per_family_member, outer_f, inner_f):
    """
    Given a map with the revenue per node per family member and two aggregation functions: outer_f, inner_f; returns the overall aggregations
    and the inner aggregations for logging purposes.
    :param revenue_per_node_per_family_member:
    :param outer_f:
    :param inner_f:
    :return:
    """
    inner_aggregation = inner_f(revenue_per_node_per_family_member)
    return float(outer_f(inner_aggregation)), inner_aggregation


def check_no_outgoing_edges(component: nx.Graph, G: nx.Graph) -> bool:
    """
    Given a connected component of a graph, returns true if it has outgoing edges, and false otherwise.
    :param component:
    :param G:
    :return:
    """
    for node in component.nodes():
        out_edges = G.out_edges(node)
        for coming, going in out_edges:
            if going not in component.nodes:
                return False
    return True


def compute_sink_eq(G: nx.Graph, revenue_per_node: Dict[str, float]) -> Tuple[List[List[str]], List[List[float]]]:
    """
    Given a BRG and a dictionary node -> revenue, returns the sinks and the revenue per node per sink.
    :param G:
    :param revenue_per_node
    :return:
    """
    # Compute strongly connected components.
    strong_components = nx.strongly_connected_component_subgraphs(G)

    # A sink is a strongly connected component of G that has no outgoing edges.
    sinks = [[v for v in n.nodes()] for n in list(filter(lambda X, base_graph=G: check_no_outgoing_edges(X, base_graph), strong_components))]

    # Compute the revenue per node per S.C.C.
    revenue_per_node_per_sink = [[revenue_per_node[node] for node in sink] for sink in sinks]

    # Return the relevant data
    return sinks, revenue_per_node_per_sink


def compute_scc_eq(G: nx.Graph, revenue_per_node: Dict[str, float]) -> Tuple[List[List[str]], List[List[float]]]:
    """
    Given a BRG and a dictionary node -> revenue, returns the strongly connected components of the BRG and a list of lists with revenue per node per sink.
    :param G:
    :param revenue_per_node:
    :return:
    """
    # Compute strongly connected components.
    strongly_connected_components = [[v for v in n] for n in nx.strongly_connected_components(G)]

    # Compute the revenue per node per S.C.C.
    revenue_per_node_per_scc = [[revenue_per_node[node] for node in scc] for scc in strongly_connected_components]

    # Return the relevant data
    return strongly_connected_components, revenue_per_node_per_scc


def save_eq_data(family_of_nodes: List[List[str]], revenue_per_node_per_family_member: List[List[float]], aggregations, file: str, verbose: bool):
    """
    Given a family of nodes, the revenue per node per family member, and aggregated data; save all of it for logging purposes.
    :param family_of_nodes:
    :param revenue_per_node_per_family_member:
    :param aggregations:
    :param file:
    :param verbose:
    :return:
    """
    final_aggregated_revenue = aggregations[0]
    aggregated_revenue_per_family_member = aggregations[1]
    # Save results to files.
    f = open(file, "w")
    f.write(str(final_aggregated_revenue) + "\n")
    for s in family_of_nodes:
        f.write(",".join(s) + "\n")
    for s in revenue_per_node_per_family_member:
        f.write(",".join([str(r) for r in s]) + "\n")
    for m in aggregated_revenue_per_family_member:
        f.write(str(m) + "\n")

    if verbose:
        print("family_of_nodes = ", family_of_nodes)
        print("revenue_per_node_per_family_member = ", revenue_per_node_per_family_member)
        print("aggregated_revenue_per_family_member = ", aggregated_revenue_per_family_member)
        print("final_aggregated_revenue = ", final_aggregated_revenue)
        # plot_directed_graph(G)
