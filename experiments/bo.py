from singletonsetup import SingletonSetup
from experiments import estimate_a_single_game
from bo_util import safe_create_dir, save_step_config_file, read_reserve_prices, read_revenue, get_gaussian, get_tuple_of_reserves, get_map_of_reserves, pretty_print_map_of_reserve
from game.structures import Good
from gt.brg import compute_eps_brg
from gt.eq import compute_scc_eq, compute_sink_eq, save_eq_data, aggregators, aggregate
from skopt import gp_minimize
from prettytable import PrettyTable
import random
import configparser
import time
import numpy as np
import sys

if len(sys.argv) > 1:
    algorithm = sys.argv[1]
else:
    algorithm = 'random'

# Some hard-coded reserve prices.
map_of_initial_reserve = {Good({"Male", "Young", "High"}, None, None): 0.0,
                          Good({"Male", "Young", "Low"}, None, None): 0.0,
                          Good({"Male", "Old", "High"}, None, None): 0.0,
                          Good({"Male", "Old", "Low"}, None, None): 0.0,
                          Good({"Female", "Young", "High"}, None, None): 0.0,
                          Good({"Female", "Young", "Low"}, None, None): 0.0,
                          Good({"Female", "Old", "High"}, None, None): 0.0,
                          Good({"Female", "Old", "Low"}, None, None): 0.0}

# Bounds on reserve price
MIN_RESERVE_PRICE = 0.0
MAX_RESERVE_PRICE = 1.5

# The experiment id. Eventually, should be read from command line.
expt_id = 'H'

# Read the experiment directory
expt_directory_base = SingletonSetup.path_to_results + f'experiment_' + expt_id + '/'

# Read the configuration file of the experiment.
expt_config = configparser.ConfigParser()
expt_config.read(expt_directory_base + 'config.ini')
k = int(expt_config['PARAMETERS']['k'])
n = int(expt_config['PARAMETERS']['n'])
reach_discount_factor = float(expt_config['PARAMETERS']['reach_discount_factor'])
eps_values = eval(expt_config['PARAMETERS']['eps_values'])
delta = float(expt_config['PARAMETERS']['delta'])
budget = int(expt_config['PARAMETERS']['budget'])
trials = int(expt_config['PARAMETERS']['trials'])

# We will perform a number of trials ...
for trial in range(trials):
    # .. For a number of epsilons.
    for eps in eps_values:
        # Create the folder for the experiment
        expt_directory = safe_create_dir(expt_directory_base + algorithm + '/eps_' + str(eps) + '/trial_' + str(trial) + '/')

        print('\n************** EMD EXPERIMENT **************')

        # Experiments parameters read from .ini file:
        print(f'Trial {trial} for algorithm: {algorithm}')
        print(f'k = {k}, n = {n}, reach_discount_factor = {reach_discount_factor}, eps = {eps}, delta = {delta}, budget = {budget}')

        # Collect all the setup into one object.
        my_setup = SingletonSetup(expt_id, k, n, reach_discount_factor, eps, delta, budget)

        # Save in the 0/ directory the config.ini file with the initial reserve prices.
        save_step_config_file(0, map_of_initial_reserve, expt_directory)

        # Keep track of the development of the experiment.
        revenue_map = {}

        # Time the experiment
        initial_time_bo = time.time()

        # Conduct the experiment.
        for i in range(0, budget):
            print(f'\n Step {i} out of {budget}')
            # Read the reserve price
            current_reserve_prices = read_reserve_prices(i, expt_directory)
            print(f'\n\t -> Running step #{i}, with reserve: \n{pretty_print_map_of_reserve(current_reserve_prices)}')
            print(f'\n\t -> Current state of the revenue function = {revenue_map}')

            # Update the setup with the experiment step and the reserve prices.
            SingletonSetup.set_reserve_prices(current_reserve_prices)
            SingletonSetup.set_expt_step(i)
            # The results directory
            results_directory = expt_directory + str(my_setup.expt_step) + '/'
            results_file = results_directory + 'results.csv'
            results_eq_file = results_directory + 'eq.txt'

            # Estimate the game.
            estimate_a_single_game(my_setup, file=results_file, serial=False)

            # Compute the BRG
            G, revenue_per_node = compute_eps_brg(file=results_file, eps=eps, normalize_revenue=True)

            # Compute the eq - In this case SCC eq.
            family_of_nodes, revenue_per_node_per_family_member = compute_scc_eq(G=G, revenue_per_node=revenue_per_node)

            # Compute the eq - In this case Sink eq.
            # family_of_nodes, revenue_per_node_per_family_member = compute_sink_eq(G=G, revenue_per_node=revenue_per_node)

            # Save the data from the equilibria to a file that can be read later.
            save_eq_data(family_of_nodes=family_of_nodes,
                         revenue_per_node_per_family_member=revenue_per_node_per_family_member,
                         aggregations=aggregate(revenue_per_node_per_family_member, aggregators['min-min'][0], aggregators['min-min'][1]),
                         file=results_eq_file,
                         verbose=False)

            # Read the value of the revenue found.
            revenue_at_step = read_revenue(i, expt_directory)
            print(f'\t Revenue at step = {revenue_at_step}')

            # Query the next point using B.O.
            revenue_map[get_tuple_of_reserves(current_reserve_prices)] = revenue_at_step
            reserves = [reserve for reserve, _ in revenue_map.items()]
            values = [revenue_map[r] for r in reserves]

            if algorithm == 'random':
                next_reserve = {g: random.random() * MAX_RESERVE_PRICE for g, _ in map_of_initial_reserve.items()}
                print(f'\t -> Next reserve price to query: \n{pretty_print_map_of_reserve(next_reserve)}')
                save_step_config_file(i + 1, next_reserve, expt_directory)
                continue

            # Compute the Gaussian error appropriately for the Hoeffding Bound
            if algorithm == 'gpn':
                gaussians = [get_gaussian(-v, delta=delta, epsilon=eps) for v in values]
                ys = [-g.mean for g in gaussians]
                alphas = np.array([g.std ** 2 for g in gaussians])
            else:
                ys = values
                alphas = 1e-10
            print(f'\t values = {values}')
            # ToDo. This is just a hack to get the next query point! Should re-think this. The gp_minimize object does not return an optimizer!.
            result, optimizer = gp_minimize(func=lambda x, the_f=revenue_map: the_f[x[0]],
                                            dimensions=[(MIN_RESERVE_PRICE, MAX_RESERVE_PRICE) for _ in range(0, 8)],
                                            n_calls=0,
                                            x0=reserves,
                                            y0=ys,
                                            n_random_starts=0,
                                            random_state=123,
                                            alpha=alphas)
            next_reserve = get_map_of_reserves(optimizer.ask())
            # print(f'-> Next reserve price to query: \n{pretty_print_map_of_reserve(next_reserve)}')
            save_step_config_file(i + 1, next_reserve, expt_directory)

        print('\n****** End of BO-EMD Experiment ****** ')

        revenue_table = PrettyTable()
        revenue_table.field_names = ['Reserve', 'Revenue']
        revenue_table.align['Reserve'] = 'l'
        revenue_table.align['Revenue'] = 'l'
        for r, rev in revenue_map.items():
            revenue_table.add_row([r, rev])
        print(revenue_table)
        print(f'\n total_time for one BO experiment with budget = {budget}  = {time.time() - initial_time_bo}')
