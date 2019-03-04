from singletonsetup import SingletonSetup
from bo_util import safe_create_dir, map_of_initial_reserve, MIN_RESERVE_PRICE, MAX_RESERVE_PRICE
import random
import configparser
import sys

if len(sys.argv) > 1:
    expt_id = sys.argv[1]
    x_init_num = int(sys.argv[2])
else:
    expt_id = 'calena'
    x_init_num = 10

# Read the experiment directory
expt_directory_base = SingletonSetup.path_to_results + f'experiment_' + expt_id + '/'

# Read the configuration file of the experiment.
expt_config = configparser.ConfigParser()
expt_config.read(expt_directory_base + 'config.ini')
eps_values = eval(expt_config['PARAMETERS']['eps_values'])
trials = int(expt_config['PARAMETERS']['trials'])

for trial in range(trials):
    for eps in eps_values:
        print(trial, eps)
        # Create the folder for the initial points of experiment
        expt_directory = safe_create_dir(f'{expt_directory_base}x_init/eps_{eps}/trial_{trial}/')

        x_init_config_file = configparser.ConfigParser()
        x_init_config_file[f'RESERVE_PRICES_META'] = {'x_init_num': x_init_num}
        x_init_config_file[f'RESERVE_PRICES_0'] = {g.id: MIN_RESERVE_PRICE for g, _ in map_of_initial_reserve.items()}
        x_init_config_file[f'RESERVE_PRICES_1'] = {g.id: MAX_RESERVE_PRICE for g, _ in map_of_initial_reserve.items()}
        for i in range(2, x_init_num):
            x_init_config_file[f'RESERVE_PRICES_{i}'] = {g.id: random.random() * MAX_RESERVE_PRICE for g, _ in map_of_initial_reserve.items()}
        with open(expt_directory + '/config.ini', 'w') as configfile:
            x_init_config_file.write(configfile)
