from singletonsetup import SingletonSetup
from experiments import estimate_a_single_game
from gt.brg import compute_eps_brg
from gt.eq import compute_scc_eq, compute_sink_eq, save_eq_data, aggregators, aggregate
from skopt import gp_minimize
from prettytable import PrettyTable
import random
import configparser
import time
import sys
from bo_util import safe_create_dir, save_step_config_file, read_reserve_prices, \
    read_revenue, get_gaussian, get_tuple_of_reserves, get_map_of_reserves, \
    pretty_print_map_of_reserve, read_reserve_prices_from_dict, \
    MIN_RESERVE_PRICE, MAX_RESERVE_PRICE, map_of_initial_reserve


def get_gp_algorithm_param(which_algorithm, the_values, the_gaussians):
    the_alphas = 1e-10
    if which_algorithm == 'gp':
        the_ys = the_values
        the_noise = 1e-10
    elif which_algorithm == 'gpm':
        the_ys = [-g.mean for g in the_gaussians]
        the_noise = 1e-10
    else:
        raise Exception(f'unknown algorithm {which_algorithm}')
    return the_ys, the_noise, the_alphas


def query_game(the_setup, the_results_dir, the_eps):
    """
    Given the setup object, the results dir and the eps, this function call other functions that
    1) simulate the game
    2) compute the eps brg
    3) save the game play data.
    :param the_setup:
    :param the_results_dir:
    :param the_eps:
    :return:
    """
    # Estimate the game.
    estimate_a_single_game(the_setup, file=the_results_dir + 'results.csv', serial=False)

    # Compute the BRG
    G, revenue_per_node = compute_eps_brg(file=the_results_dir + 'results.csv', eps=the_eps, normalize_revenue=True)

    # Compute the eq - In this case SCC eq.
    family_of_nodes, revenue_per_node_per_family_member = compute_scc_eq(G=G, revenue_per_node=revenue_per_node)

    # Compute the eq - In this case Sink eq.
    # family_of_nodes, revenue_per_node_per_family_member = compute_sink_eq(G=G, revenue_per_node=revenue_per_node)

    # Save the data from the equilibria to a file that can be read later.
    save_eq_data(family_of_nodes=family_of_nodes,
                 revenue_per_node_per_family_member=revenue_per_node_per_family_member,
                 aggregations=aggregate(revenue_per_node_per_family_member, aggregators['min-min'][0], aggregators['min-min'][1]),
                 file=the_results_dir + 'eq.txt',
                 verbose=False)


if len(sys.argv) > 1:
    expt_id = sys.argv[1]
    algorithm = sys.argv[2]
    start_trial = int(sys.argv[3])
else:
    expt_id = 'calena'
    algorithm = 'gpm'
    start_trial = 2

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
for trial in range(start_trial, trials):
    # .. For a number of epsilons.
    for eps in eps_values:
        # Create the folder for the experiment
        expt_directory = safe_create_dir(expt_directory_base + algorithm + '/eps_' + str(eps) + '/trial_' + str(trial) + '/', False)

        # print('\n************** EMD EXPERIMENT **************')

        # Experiments parameters read from .ini file:
        print(f'Experiment {expt_id}, trial {trial} for algorithm: {algorithm}, eps = {eps}')
        # print(f'k = {k}, n = {n}, reach_discount_factor = {reach_discount_factor}, eps = {eps}, delta = {delta}, budget = {budget}')

        # Collect all the setup into one object.
        my_setup = SingletonSetup(expt_id, k, n, reach_discount_factor, eps, delta, budget)

        # Keep track of the development of the experiment.
        revenue_map = {}

        # Time the experiment
        initial_time_bo = time.time()

        # Compute the initial points first
        x_init_config_file = configparser.ConfigParser()
        x_init_config_file.read(f'{expt_directory_base}x_init/eps_{eps}/trial_{trial}/config.ini')
        x_init_num = int(x_init_config_file['RESERVE_PRICES_META']['x_init_num'])
        for i in range(0, x_init_num - 1):
            init_x_folder_index = i - x_init_num + 1
            print(f'\t Step {init_x_folder_index} out of {x_init_num} initial')
            # print(f'Reading initial reserves prices #{i}, in folder {init_x_folder_index}')
            # Update the setup with the experiment step and the reserve prices.
            the_init_reserve = read_reserve_prices_from_dict(x_init_config_file[f'RESERVE_PRICES_{i}'])
            # print(f'-> Init reserve price {i} to query: \n{pretty_print_map_of_reserve(the_init_reserve)}')
            SingletonSetup.set_reserve_prices(the_init_reserve)
            SingletonSetup.set_expt_step(init_x_folder_index)
            safe_create_dir(f'{expt_directory}{init_x_folder_index}', False)
            query_game(my_setup, expt_directory + str(my_setup.expt_step) + '/', eps)
            save_step_config_file(init_x_folder_index, the_init_reserve, expt_directory, False)
            revenue_at_step = read_revenue(init_x_folder_index, expt_directory)
            # print(f'\t Revenue for this initial reserve = {revenue_at_step}')
            revenue_map[get_tuple_of_reserves(the_init_reserve)] = revenue_at_step

        # Initialize the 0 step with the last random initial point
        save_step_config_file(0, read_reserve_prices_from_dict(x_init_config_file[f'RESERVE_PRICES_{x_init_num - 1}']), expt_directory, False)

        # Conduct the experiment.
        for i in range(0, budget):
            print(f'\t Step {i} out of {budget}, eps = {eps}')
            # Read the reserve price
            current_reserve_prices = read_reserve_prices(i, expt_directory)
            # print(f'\n\t -> Running step #{i}, with reserve: \n{pretty_print_map_of_reserve(current_reserve_prices)}')
            # print(f'\n\t -> Current state of the revenue function = {revenue_map}')

            # Update the setup with the experiment step and the reserve prices.
            SingletonSetup.set_reserve_prices(current_reserve_prices)
            SingletonSetup.set_expt_step(i)
            query_game(my_setup, expt_directory + str(my_setup.expt_step) + '/', eps)

            # Read the value of the revenue found.
            revenue_at_step = read_revenue(i, expt_directory)
            # print(f'\t Revenue at step = {revenue_at_step}')

            # Query the next point using some search strategy. As of now, we have Random and B.O.
            revenue_map[get_tuple_of_reserves(current_reserve_prices)] = revenue_at_step
            reserves = [reserve for reserve, _ in revenue_map.items()]
            values = [revenue_map[r] for r in reserves]

            if algorithm == 'random':
                next_reserve = {g: random.random() * MAX_RESERVE_PRICE for g, _ in map_of_initial_reserve.items()}
            else:
                # Compute the Gaussian error appropriately for the Hoeffding's like bounds
                gaussians = [get_gaussian(-v, delta=delta, epsilon=eps) for v in values]
                ys, noise, alphas = get_gp_algorithm_param(algorithm, values, gaussians)
                # ToDo. This is just a hack to get the next query point! Should re-think this. The gp_minimize object does not return an optimizer!.
                result, optimizer = gp_minimize(func=None,  # There is no function here! We just use this function to query the next point.,
                                                dimensions=[(MIN_RESERVE_PRICE, MAX_RESERVE_PRICE) for _ in range(0, 8)],
                                                base_estimator=None,
                                                n_calls=0,
                                                n_random_starts=0,
                                                acq_func='EI',
                                                acq_optimizer='lbfgs',
                                                x0=reserves,
                                                y0=ys,
                                                random_state=123,
                                                verbose=False,
                                                callback=None,
                                                n_points=10000,
                                                n_restarts_optimizer=5,
                                                xi=0.01,
                                                kappa=None,
                                                noise=noise,
                                                n_jobs=-1,
                                                alpha=alphas)
                next_reserve = get_map_of_reserves(optimizer.ask())
            # Save the results.
            save_step_config_file(i + 1, next_reserve, expt_directory, False)

        # print('\n****** End of EMD Experiment ****** ')

        # revenue_table = PrettyTable()
        # revenue_table.field_names = ['Reserve', 'Revenue']
        # revenue_table.align['Reserve'] = 'l'
        # revenue_table.align['Revenue'] = 'l'
        # for r, rev in revenue_map.items():
        #    revenue_table.add_row([r, rev])
        # print(revenue_table)
        # print(f'\n total_time for one BO experiment with budget = {budget}  = {time.time() - initial_time_bo}')
