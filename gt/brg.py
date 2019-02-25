import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def plot_directed_graph(G: nx.Graph):
    """
    Plots a directed graph in a circular layout.
    :param G:
    :return:
    """
    pos = nx.circular_layout(G)
    nx.draw(G, pos, node_size=3200, with_labels=True)
    plt.show()


def compute_eps_brg(file: str, eps: float = 0.0, normalize_revenue=False, verbose: bool = False):
    """
    Reads the results.csv file, constructs the 2eps-BRG and returns it, together with the revenue at each node.
    :param file:
    :param eps:
    :param normalize_revenue:
    :param verbose:
    :return:
    """
    # Read the results and compute the mean utility
    data = pd.read_csv(file)

    # Normalize the utilities to be in the 0-1 range
    data['we'] = data['we'].apply(lambda x, the_max=max(data['we']), the_min=min(data['we']): (x - the_min) / ((the_max - the_min) if the_max - the_min > 0.0 else 1.0))
    data['wf'] = data['wf'].apply(lambda x, the_max=max(data['wf']), the_min=min(data['wf']): (x - the_min) / ((the_max - the_min) if the_max - the_min > 0.0 else 1.0))
    if normalize_revenue:
        data['revenue'] = data['revenue'].apply(
            lambda x, the_max=max(data['revenue']), the_min=min(data['revenue']): (x - the_min) / ((the_max - the_min) if the_max - the_min > 0.0 else 1.0))

    # Aggregate data by mean.
    mean = data.groupby(by=['num_WE', 'num_WF']).mean()
    mean = mean.reset_index()
    n = int(data.iloc[0]['num_WE']) + int(data.iloc[0]['num_WF'])

    # Create the best-response graph object.
    G = nx.DiGraph()
    # Nodes are strategy profiles.
    G.add_nodes_from([str(k) + 'WE_' + str(n - k) + 'WF' for k in range(0, n + 1)])
    we_utilities = {int(row['num_WE']): row['we'] for index, row in mean.iterrows()}
    wf_utilities = {int(row['num_WF']): row['wf'] for index, row in mean.iterrows()}
    # Record the revenue.
    revenue = {str(int(row['num_WE'])) + 'WE_' + str(n - int(row['num_WE'])) + 'WF': row['revenue'] for index, row in mean.iterrows()}

    # With a single linear pass over the nodes, we can determine the edges.
    for i in range(0, n + 1):
        if i < n:
            # Debug print info
            if verbose:
                print('\n', i, we_utilities[i + 1], wf_utilities[n - i], end='')
                if we_utilities[i + 1] >= wf_utilities[n - i] - 2.0 * eps:
                    print("\t->", end='')
                if we_utilities[i + 1] - 2.0 * eps <= wf_utilities[n - i]:
                    print("\t<-", end='')
                print("\t 2eps = ", 2.0 * eps, end='')

            # Forward pass: I was playing WF but want to play WE now (up to 2 epsilon)
            if we_utilities[i + 1] >= wf_utilities[n - i] - 2.0 * eps:
                G.add_edge(str(i) + 'WE_' + str(n - i) + 'WF', str(i + 1) + 'WE_' + str(n - i - 1) + 'WF')
            # Backward pass: I was playing WE but want to play WF now  (up to 2 epsilon)
            if we_utilities[i + 1] - 2.0 * eps <= wf_utilities[n - i]:
                G.add_edge(str(i + 1) + 'WE_' + str(n - i - 1) + 'WF', str(i) + 'WE_' + str(n - i) + 'WF')

    if verbose:
        plot_directed_graph(G)
    return G, revenue
