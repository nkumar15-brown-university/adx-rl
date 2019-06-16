import configparser
import math
import random
import sys

import numpy as np
import pandas as pd
from skopt import gp_minimize

from .bo_util import get_gaussian, get_gp_algorithm_param, safe_create_dir
from .fpa import f, compute_strategy_uniform_case, compute_m

if len(sys.argv) > 1:
    expt_id = sys.argv[1]
    algorithm = sys.argv[2]
else:
    expt_id = 'fpa'
    algorithm = 'gpn'

expt_directory_base = f'../results/experiments/{expt_id}/'

expt_config = configparser.ConfigParser()
expt_config.read(expt_directory_base + 'config.ini')
eps_values = eval(expt_config['PARAMETERS']['eps_values'])
delta = float(expt_config['PARAMETERS']['delta'])
budget = int(expt_config['PARAMETERS']['budget'])
trials = int(expt_config['PARAMETERS']['trials'])
n = 2

which_strategies = lambda r, v, n: compute_strategy_uniform_case(r, v, n)
which_val_distri = lambda n: np.random.uniform(0, 1, n)

# We will perform a number of trials ...
for trial in range(0, trials):
    # .. For a number of epsilons.
    for eps in eps_values:
        m = math.ceil(compute_m(delta, eps, n))
        # Keep track of the development of the experiment.
        revenue_map = {}
        final_result = []

        # Create the folder for the experiment
        expt_directory = safe_create_dir(expt_directory_base + algorithm + '/eps_' + str(eps) + '/trial_' + str(trial) + '/', False)

        # print('\n************** EMD EXPERIMENT **************')

        # Read initial random points
        x_init_config_file = configparser.ConfigParser()
        x_init_config_file.read(f'{expt_directory_base}x_init/eps_{eps}/trial_{trial}/config.ini')
        print(f'{expt_directory_base}x_init/eps_{eps}/trial_{trial}/config.ini')
        x_init_num = int(x_init_config_file['RESERVE_PRICES_META']['x_init_num'])
        for i in range(0, x_init_num):
            the_init_reserve = float(x_init_config_file[f'RESERVE_PRICES'][str(i)])
            print(f'\t Step {i} out of {x_init_num} initial, reserve = {the_init_reserve}')
            revenue_map[the_init_reserve] = f(which_val_distri, which_strategies, None, m, n, None)(the_init_reserve)
            final_result += [(i - x_init_num, the_init_reserve, revenue_map[the_init_reserve])]

        # Experiments parameters read from .ini file:
        print(f'Experiment {expt_id}, trial {trial} for algorithm: {algorithm}, eps = {eps}')
        # Conduct the experiment.
        for i in range(0, budget):
            print(f'\t Step {i} out of {budget}, eps = {eps}')
            if algorithm == 'random':
                next_reserve = random.random()
            else:
                # Compute the Gaussian error appropriately for the Hoeffding's like bounds
                reserves = [reserve for reserve, _ in revenue_map.items()]
                values = [revenue_map[r] for r in reserves]
                gaussians = [get_gaussian(-v, delta=delta, epsilon=eps) for v in values]
                ys, noise, alphas = get_gp_algorithm_param(algorithm, values, gaussians)
                # Bayesian optimization takes this format for the x values.
                reserves = [[r] for r in reserves]
                # ToDo. This is just a hack to get the next query point! Should re-think this. The gp_minimize object does not return an optimizer!.
                result, optimizer = gp_minimize(func=None,  # There is no function here! We just use this function to query the next point.,
                                                dimensions=[(0.0, 1.0)],
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
                next_reserve = optimizer.ask()[0]
            revenue_map[next_reserve] = f(which_val_distri, which_strategies, None, m, n, None)(next_reserve)
            final_result += [(i, next_reserve, revenue_map[next_reserve])]
        revenue_df = pd.DataFrame(final_result, columns=['step', 'reserve', 'revenue'])
        revenue_df.to_csv(f'{expt_directory_base}{algorithm}/eps_{eps}/trial_{trial}/result.csv')
