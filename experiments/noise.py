import matplotlib.pyplot as plt
import pandas as pd
import math
import numpy as np
from skopt import gp_minimize
from prettytable import PrettyTable
from bo_util import get_gaussian
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import sys
import warnings

warnings.filterwarnings("ignore")


def number_of_samples(eps, delta, budget):
    return math.ceil(0.5 * ((1.0 / math.pow(eps, 2.0)) * math.log(2.0 * budget) / delta))


def f(x):
    return (((110.0 * x * (math.pow(1.0 - x, 9.0))) / (4261625379.0 / 1000000000.0)) / 2.0) - 0.25


def sample_f(x):
    return f(x) + np.random.uniform(-0.25, 0.25)


def mean_sample(x, n):
    return -np.mean(np.array([sample_f(x) for _ in range(0, n)]))


def plot_stuff():
    fig, axs = plt.subplots(ncols=3, nrows=1)

    grid = np.linspace(0, 1.0, 150)
    axs[0].plot(grid, [-f(x) for x in grid])
    axs[1].plot(grid, [-sample_f(x) for x in grid])
    axs[2].plot(grid, [mean_sample(x, number_of_samples(0.15, 0.1, 150)) for x in grid])
    plt.show()


def print_current_state(xs, values):
    revenue_table = PrettyTable()
    revenue_table.field_names = ['x', 'y']
    revenue_table.align['x'] = 'l'
    revenue_table.align['y'] = 'l'
    for x, r in zip(xs, values):
        revenue_table.add_row([x, r])
    print(revenue_table)


def get_gp_algorithm_param(which_algorithm, the_values, the_gaussians):
    the_alphas = 1e-10
    if which_algorithm == 'gp':
        the_ys = the_values
        the_noise = 1e-10
    elif which_algorithm == 'gpnoisy':
        the_ys = the_values
        the_noise = 'gaussian'
    elif which_algorithm == 'gpm':
        the_ys = [g.mean for g in the_gaussians]
        the_noise = 1e-10
    elif which_algorithm == 'gpmnoisy':
        the_ys = [g.mean for g in the_gaussians]
        the_noise = 'gaussian'
    elif which_algorithm == 'gpn':
        the_ys = [g.mean for g in the_gaussians]
        the_noise = 1e-10
        the_alphas = np.array([g.std ** 2 for g in the_gaussians])
    return the_ys, the_noise, the_alphas


def run_one_experiment(the_eps, the_delta, the_num_of_initial_points):
    m = number_of_samples(eps=the_eps, delta=the_delta, budget=budget)
    inner_results = []
    for trial in range(0, 10):
        # Initial points
        initial_xs = [[np.random.uniform(0, 1)] for _ in range(0, the_num_of_initial_points)]
        initial_xs_values = np.array([mean_sample(x[0], m) for x in initial_xs])

        for algorithm in ['gp', 'gpnoisy', 'gpm', 'gpmnoisy', 'gpn', 'random']:
            print(f"\n* algorithm = {algorithm}, ")
            # print(f"* initial_xs = {initial_xs}")
            # print(f"* initial_xs_values = {initial_xs_values}")
            # Start the algorithm at the same place.
            xs = initial_xs.copy()
            values = initial_xs_values.copy()
            inner_results += [(the_eps, the_delta, algorithm, trial, the_num_of_initial_points, -1, float(x[0]), y) for x, y in zip(xs, values)]

            for b in range(0, budget):
                print(f"\rt = {trial}, b = {b}, eps = {the_eps}, delta = {the_delta}, the_num_of_initial_points = {the_num_of_initial_points}, m = {m} ", end="")
                # print_current_state(xs, values)
                gaussians = [get_gaussian(v, delta=the_delta, epsilon=the_eps / 2.0, c_min=-0.5, c_max=0.5) for v in values]
                if algorithm == 'random':
                    next_point = [np.random.uniform(0, 1)]
                else:
                    # Get the parameters of the algorithm
                    ys, noise, alphas = get_gp_algorithm_param(algorithm, values, gaussians)
                    _, optimizer = gp_minimize(func=None,  # There is no function here! We just use this function to query the next point.
                                               dimensions=[(0.0, 1.0)],
                                               base_estimator=None,
                                               n_calls=0,
                                               n_random_starts=0,
                                               acq_func='EI',
                                               acq_optimizer='lbfgs',
                                               x0=xs,
                                               y0=ys,
                                               random_state=123,
                                               verbose=False,
                                               callback=None,
                                               n_points=10000,
                                               n_restarts_optimizer=5,
                                               xi=0.01,
                                               kappa=None,
                                               noise=noise,
                                               # n_jobs=-1, # This does not play well with the grid!
                                               alpha=alphas)
                    next_point = optimizer.ask()

                xs += [next_point]
                next_value = mean_sample(next_point[0], m)
                values = np.append(values, np.array(next_value))
                inner_results += [(the_eps, the_delta, algorithm, trial, the_num_of_initial_points, b, float(xs[b + the_num_of_initial_points][0]), next_value)]
        print(f"\n Ended trial #{trial} for: eps = {the_eps}, delta = {the_delta}, the_num_of_initial_points = {the_num_of_initial_points}, m = {m}")
    return inner_results


# In case we want to see the function.
# plot_stuff()

# Experiments Fixed parameters
budget = 20
if len(sys.argv) > 1:
    num_of_initial_points = int(sys.argv[1])
else:
    num_of_initial_points = 2

results = []
with ProcessPoolExecutor(cpu_count()) as executor:
    t = 0
    futures = []
    for eps in [0.03, 0.02, 0.01]:
        for delta in [0.3, 0.2, 0.1]:
            # for eps in [0.89, 0.9]:
            #    for delta in [0.5, 0.45]:
            futures.append(executor.submit(run_one_experiment, eps, delta, num_of_initial_points))
            t += 1
    print(f'submitted {t} jobs', flush=True)

for future in as_completed(futures):
    exp = future.exception()
    if exp is not None:
        print("An exception occurred:", exp)
        raise Exception("Something went wrong with one worker")
    else:
        result = future.result()
        results.extend(result)
results_dataframe = pd.DataFrame(results, columns=['eps', 'delta', 'algo', 'trial', 'num_init_x', 'b', 'x', 'value'])
print(results_dataframe)
results_dataframe.to_csv('../results/small_bo_' + str(num_of_initial_points) + '.csv')

# t0 = time.time()
# run_one_experiment(m=m, num_of_initial_points=num_of_initial_points)
# print(time.time() - t0)
# plot_stuff()
