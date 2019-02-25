import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()
n = 8


def get_node(num_we, num_wf):
    return str(num_we) + 'WE_' + str(num_wf) + 'WF'


def get_brg_1():
    G.add_nodes_from([str(k) + 'WE_' + str(n - k) + 'WF' for k in range(0, n + 1)])

    G.add_edge(get_node(0, 8), get_node(1, 7))
    G.add_edge(get_node(1, 7), get_node(2, 6))
    G.add_edge(get_node(2, 6), get_node(3, 5))
    G.add_edge(get_node(3, 5), get_node(2, 6))
    G.add_edge(get_node(4, 4), get_node(3, 5))
    G.add_edge(get_node(4, 4), get_node(5, 3))
    G.add_edge(get_node(5, 3), get_node(6, 2))
    G.add_edge(get_node(7, 1), get_node(6, 2))
    G.add_edge(get_node(8, 0), get_node(7, 1))

    pos = nx.circular_layout(G)
    nx.draw(G, pos, node_size=3400, with_labels=True, font_color='w')

    nx.draw_networkx_nodes(G, pos, nodelist=[get_node(0, 8), get_node(1, 7), get_node(4, 4), get_node(5, 3), get_node(7, 1), get_node(8, 0)], node_color='b', node_size=3400)
    nx.draw_networkx_nodes(G, pos, nodelist=[get_node(2, 6), get_node(3, 5), get_node(6, 2)], node_color='b', node_size=3400, alpha=0.25)

    plt.show()


def get_brg_2():
    G.add_nodes_from([str(k) + 'WE_' + str(n - k) + 'WF' for k in range(0, n + 1)])

    G.add_edge(get_node(0, 8), get_node(1, 7))
    G.add_edge(get_node(1, 7), get_node(2, 6))
    G.add_edge(get_node(2, 6), get_node(3, 5))
    G.add_edge(get_node(3, 5), get_node(4, 4))
    G.add_edge(get_node(4, 4), get_node(5, 3))
    G.add_edge(get_node(5, 3), get_node(6, 2))
    G.add_edge(get_node(6, 2), get_node(7, 1))
    G.add_edge(get_node(7, 1), get_node(8, 0))

    pos = nx.circular_layout(G)
    nx.draw(G, pos, node_size=3400, with_labels=True, font_color='w')

    nx.draw_networkx_nodes(G, pos, nodelist=[get_node(0, 8),
                                             get_node(1, 7),
                                             get_node(2, 6),
                                             get_node(3, 5),
                                             get_node(4, 4),
                                             get_node(5, 3),
                                             get_node(6, 2),
                                             get_node(7, 1)], node_color='b', node_size=3400)
    nx.draw_networkx_nodes(G, pos, nodelist=[get_node(8, 0)], node_color='b', node_size=3400, alpha=0.25)

    plt.show()


get_brg_2()
