import matplotlib.pyplot as plt
from gt.brg import compute_eps_brg
from gt.eq import compute_scc_eq, compute_sink_eq, aggregators, aggregate

# Parameters of the experiment
# x_axis = [round(0.03 * i, 2) for i in range(0, 51)]
x_axis = [round(0.01 * i, 2) for i in range(0, 151)]
aggregated_data = {name: [] for name, _ in aggregators.items()}
normalize_revenue = True
which_eq = "SCC"
which_folder = 'grid_revenue_150'

for i in range(0, 151):
    # for i in range(0, 51):
    print("\r", i, end='')
    # Compute the eps-BRG from the game data
    G, revenue_per_node = compute_eps_brg('../results/experiments/' + str(which_folder) + '/' + str(i) + '/results.csv', eps=0.025, normalize_revenue=normalize_revenue)

    # Compute the Equilibria
    family_of_nodes, revenue_per_node_per_family_member = \
        compute_scc_eq(G=G, revenue_per_node=revenue_per_node) if which_eq == "SCC" else compute_sink_eq(G=G, revenue_per_node=revenue_per_node)

    for name, (outer_f, inner_f) in aggregators.items():
        aggregated_data[name] += [aggregate(revenue_per_node_per_family_member, outer_f, inner_f)[0]]

for name, data in aggregated_data.items():
    plt.plot(x_axis, data, label=name)
    if normalize_revenue:
        plt.fill_between(x_axis, [d - 0.025 for d in data], [d + 0.025 for d in data], alpha=.5)
plt.legend()
plt.title("Revenue as a function of a single reserve price. Equilibria = " + str(which_eq))
plt.show()
