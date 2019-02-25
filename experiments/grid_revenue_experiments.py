from singletonsetup import SingletonSetup
from experiments import estimate_a_single_game
import configparser
import os as os
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import time


def run(r: float, t: int):
    # Read the experiment directory
    expt_directory = SingletonSetup.path_to_results + 'grid_revenue/'

    # Read the configuration file of the experiment.
    expt_config = configparser.ConfigParser()
    expt_config.read(expt_directory + 'config.ini')
    k = int(expt_config['PARAMETERS']['k'])
    n = int(expt_config['PARAMETERS']['n'])
    reach_discount_factor = float(expt_config['PARAMETERS']['reach_discount_factor'])
    eps = float(expt_config['PARAMETERS']['eps'])
    delta = float(expt_config['PARAMETERS']['delta'])
    budget = int(expt_config['PARAMETERS']['budget'])

    print("\n************** GRID REVENUE EXPERIMENT **************")
    # Collect all the setup into one object.
    my_setup = SingletonSetup(-1, k, n, reach_discount_factor, eps, delta, budget)

    # Update the setup with the experiment step and the reserve prices.
    SingletonSetup.set_expt_step(t)
    SingletonSetup.set_reserve_prices(r)

    # Set the results directory
    results_directory = my_setup.path_to_results + 'grid_revenue/' + str(my_setup.expt_step) + '/'

    # Experiments parameters read from .ini file:
    print("results_directory = ", results_directory, flush=True)
    print("t = ", t, "r = ", r, " k = ", k, ", n = ", n, ", reach_discount_factor = ", reach_discount_factor,
          ", eps = ", eps, ", delta = ", delta, ", budget = ", budget, flush=True)

    # Create the result directory
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)
    results_file = results_directory + 'results.csv'
    estimate_a_single_game(my_setup, file=results_file)


def main():
    serial = False
    # Run experiments with a grid of reserve prices.
    if serial:
        t = 0
        for r in [round(0.01 * i, 2) for i in range(0, 151)]:
            run(r=r, t=t)
            t += 1
    else:
        with ProcessPoolExecutor(cpu_count()) as executor:
            t = 0
            futures = []
            for r in [round(0.01 * i, 2) for i in range(0, 151)]:
                # for r in [round(0.03 * i, 2) for i in range(0, 51)]:
                futures.append(executor.submit(run, r, t))
                t += 1
            print(f'submitted {t} jobs', flush=True)
            for future in as_completed(futures):
                exp = future.exception()
                if exp is not None:
                    print("An exception occurred:", exp)
                    raise Exception("Something went wrong with one worker")


if __name__ == '__main__':
    t0 = time.time()
    main()
    t1 = time.time()
    print("\n ******** DONE *************")
    print("Took: ", t1 - t0)
