import configparser
import random
import sys

from .bo_util import safe_create_dir

if len(sys.argv) > 1:
    expt_id = sys.argv[1]
    x_init_num = int(sys.argv[2])
else:
    expt_id = 'fpa'
    x_init_num = 3

# Read the experiment directory
expt_directory_base = f'../results/experiments/{expt_id}/'

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
        x_init_config_file[f'RESERVE_PRICES'] = {"0": 0.0, "1": 1.0}
        for i in range(2, x_init_num):
            x_init_config_file[f'RESERVE_PRICES'][str(i)] = str(random.random())
        with open(expt_directory + '/config.ini', 'w') as configfile:
            x_init_config_file.write(configfile)
