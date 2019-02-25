import random

from singletonsetup import SingletonSetup
from experiments import estimate_a_single_game
from gt.brg import compute_eps_brg
from gt.eq import compute_scc_eq, compute_sink_eq, save_eq_data, aggregators, aggregate
from skopt import gp_minimize
from prettytable import PrettyTable
from collections import namedtuple
import configparser
import os as os
import math
import time
import numpy as np
import sys

if len(sys.argv) > 1:
    algorithm = sys.argv[1]
else:
    algorithm = 'gp'


Gaussian = namedtuple('Gaussian', ['mean', 'std'])

MAX_RESERVED_PRICE = 1.5

def get_gaussian(center: float, delta: float, epsilon: float, c_min: float = 0.0, c_max: float = 1.0) -> Gaussian:
    c0, c1, c2, c3 = c_min, center - epsilon, center + epsilon, c_max
    d = delta
    if c1 < c0:
        c1 = c0
    if c2 > c3:
        c2 = c3
    # assert c_min <= c1 <= c2 <= c_max, f'Cannot satisfy: {c_min} <= {c1} <= {c2} <= {c_max} for (c={center}, epsilon={epsilon})'
    if c1 == c2:
        return Gaussian(c1, 0.0)
    dc = (c1 - c0) ** 2 + (c3 - c2) ** 2
    if dc < 1e-12:
        g1, g2, g3 = 0.0, 1.0, 0.0
    else:
        g1 = d * (c1 - c0) / dc
        g2 = (1 - d) / (c2 - c1)
        g3 = d * (c3 - c2) / dc
    m2 = g1 * (c1 + c0) * (c1 - c0) / 2 + g2 * (c1 + c2) * (c2 - c1) / 2 + g3 * (c3 - c2) * (c3 + c2) / 2

    def sig(c):
        return (c * c * c) / 3 - m2 * (c * c) + (m2 * m2) * c

    s2 = g1 * (sig(c1) - sig(c0))
    s2 += g2 * (sig(c2) - sig(c1))
    s2 += g3 * (sig(c3) - sig(c2))
    s2 = math.sqrt(s2)
    return Gaussian(m2, s2)


def save_step_config_file(step: int, single_reserve: float):
    config_file = configparser.ConfigParser()
    config_file['RESERVE_PRICES'] = {'single_reserve': single_reserve}
    if not os.path.exists(expt_directory + str(step) + "/"):
        os.makedirs(expt_directory + str(step) + "/")
    else:
        raise Exception("The " + str(step) + "/ directory already exists, stopping the experiment")
    with open(expt_directory + str(step) + '/config.ini', 'w') as configfile:
        config_file.write(configfile)


def read_reserve_price(step: int):
    config_file = configparser.ConfigParser()
    config_file.read(expt_directory + str(step) + '/config.ini')
    return float(config_file['RESERVE_PRICES']['single_reserve'])


def read_revenue(step: int):
    with open(expt_directory + str(step) + '/eq.txt') as f:
        revenue = float(f.readline())
    return -revenue


# The normalization constant. Revenue goes from 0, and in the case of experiments so far, it goes to about 150.0
# ToDo: this needs to be changed for different experimental setups
revenue_normalization = 150.0
# The experiment id. Eventually, should be read from command line.
expt_id = 'Z'
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

for trial in range(trials):
    for eps in eps_values:
        expt_directory = expt_directory_base + algorithm + '/eps_' + str(eps) + '/trial_' + str(trial) + '/'
        os.makedirs(expt_directory)
        print("\n************** EMD EXPERIMENT **************")
        # Experiments parameters read from .ini file:
        print("k = ", k, ", n = ", n, ", reach_discount_factor = ", reach_discount_factor, ", eps = ", eps, ", delta = ", delta, ", budget = ", budget)
        print(f'Trial {trial} for algorithm: {algorithm}')

        # Find the next step to perform.
        list_of_indeces = list(filter(lambda d: d.split('/')[-1].isdigit(), [x[0] for x in os.walk(expt_directory)]))
        list_of_indeces.sort(key=lambda x: int(x.split('/')[-1]), reverse=True)
        next_i = 0 if len(list_of_indeces) == 0 else int(list_of_indeces[0].split('/')[-1])
        if next_i == budget:
            print("\n\n Experiment done!")
            exit()

        # Keep track of the development of the experiment.
        revenue_map = {}

        # If this is the first experiment, then initialize stuff.
        if next_i == 0:
            initial_single_reserve = random.random() * MAX_RESERVED_PRICE
            print("\t\t Note: starting with all " + str(initial_single_reserve) + " reserve prices. ")
            # To start: we will do a single reserve price equal to the halfway point (1.5 + .5) / 2 = 1.0, of the expected bids.
            save_step_config_file(0, initial_single_reserve)
        else:
            # Read and collect all previous results.
            for i in range(0, next_i):
                read_reserve_price(i)
                revenue_map[read_reserve_price(i)] = read_revenue(i)

        # Collect all the setup into one object.
        my_setup = SingletonSetup(expt_id, k, n, reach_discount_factor, eps, delta, budget)

        t0 = time.time()
        # Conduct the experiment.
        for i in range(next_i, budget):
            print("\tStep number ", i, " out of ", budget)
            # Read the reserve price
            current_reserve_price = read_reserve_price(i)
            print("\n -> Running step #" + str(i) + ", with reserve: " + str(current_reserve_price))
            print("\n Current state of the revenue function = ", revenue_map)

            # Update the setup with the experiment step and the reserve prices.
            SingletonSetup.set_reserve_prices(current_reserve_price)
            SingletonSetup.set_expt_step(i)
            # The results directory
            results_directory = expt_directory + str(my_setup.expt_step) + '/'
            results_file = results_directory + 'results.csv'
            results_eq_file = results_directory + 'eq.txt'

            # Estimate the game.
            estimate_a_single_game(my_setup, file=results_file, serial=False)

            # Compute the BRG
            G, revenue_per_node = compute_eps_brg(file=results_file, eps=eps)

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
            revenue_at_step = read_revenue(i)
            revenue_at_step = revenue_at_step / revenue_normalization
            print("\t Revenue at step = ", revenue_at_step)

            # Query the next point using B.O.
            revenue_map[current_reserve_price] = revenue_at_step
            reserves = [[reserve] for reserve, _ in revenue_map.items()]
            values = [revenue_map[r[0]] for r in reserves]

            if algorithm == 'random':
                next_reserve = random.random() * MAX_RESERVED_PRICE
                print("\t -> Next reserve price to query:", next_reserve)
                save_step_config_file(i + 1, next_reserve)
                continue

            # Compute the Gaussian error appropriately for the Hoeffding Bound
            if algorithm == 'gpn':
                gaussians = [get_gaussian(-v, delta=delta, epsilon=eps) for v in values]
                ys = [-g.mean for g in gaussians]
                alphas = np.array([g.std ** 2 for g in gaussians])
            else:
                ys = values
                alphas = 1e-10
            print("values = ", values)
            # ToDo. This is just a hack to get the next query point! Should re-think this.
            # ToDo. The gp_minimize object does not return an optimizer!.
            result, optimizer = gp_minimize(func=lambda x, the_f=revenue_map: the_f[x[0]],
                                            dimensions=[(0.0, MAX_RESERVED_PRICE)],
                                            n_calls=0,
                                            x0=reserves,
                                            y0=ys,
                                            n_random_starts=0,
                                            random_state=123,
                                            alpha=alphas)
            next_reserve = optimizer.ask()
            print("\t -> Next reserve price to query:", next_reserve)
            save_step_config_file(i + 1, next_reserve[0])

        print("\n****** End of BO-EMD Experiment ****** ")

        revenue_table = PrettyTable()
        revenue_table.field_names = ['Reserve', 'Revenue']
        revenue_table.align['Reserve'] = "l"
        revenue_table.align['Revenue'] = "l"
        for r, rev in revenue_map.items():
            revenue_table.add_row([r, rev])
        print(revenue_table)
        t1 = time.time()
        total_time = t1 - t0
        print("\n total_time = ", total_time)
