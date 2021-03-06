import configparser
import math
import os as os
from collections import namedtuple
from typing import Dict, Tuple

import numpy as np
from prettytable import PrettyTable

from game.structures import Good

# Bounds on reserve price
MIN_RESERVE_PRICE = 0.0
MAX_RESERVE_PRICE = 1.5

# Some dummy reserve prices.
map_of_initial_reserve = {Good({"Male", "Young", "High"}, None, None): 0.0,
                          Good({"Male", "Young", "Low"}, None, None): 0.0,
                          Good({"Male", "Old", "High"}, None, None): 0.0,
                          Good({"Male", "Old", "Low"}, None, None): 0.0,
                          Good({"Female", "Young", "High"}, None, None): 0.0,
                          Good({"Female", "Young", "Low"}, None, None): 0.0,
                          Good({"Female", "Old", "High"}, None, None): 0.0,
                          Good({"Female", "Old", "Low"}, None, None): 0.0}

# We need some structure to keep an ordering of the different market segments.
ordered_segments = [('Male', 'Young', 'High'),
                    ('Male', 'Young', 'Low'),
                    ('Male', 'Old', 'High'),
                    ('Male', 'Old', 'Low'),
                    ('Female', 'Young', 'High'),
                    ('Female', 'Young', 'Low'),
                    ('Female', 'Old', 'High'),
                    ('Female', 'Old', 'Low')]
Gaussian = namedtuple('Gaussian', ['mean', 'std'])

# Since the has of a good is by the first letter of segments, we need this map to convert between reserves prices store in config file and a map.
letter_to_segment = {'f': 'Female', 'm': 'Male', 'h': 'High', 'l': 'Low', 'y': 'Young', 'o': 'Old'}


def read_reserve_prices_from_dict(map_of_reserve: Dict[str, float]) -> Dict[Good, float]:
    reserve_map = {}
    for market, reserve in map_of_reserve.items():
        reserve_map[Good({letter_to_segment[l] for l in market}, None, None)] = float(reserve)
    return reserve_map


def read_reserve_prices(step: int, expt_directory: str) -> Dict[Good, float]:
    """
    Given a step of the experiment, read the reserve prices from the corresponding config.ini file
    :param step:
    :param expt_directory:
    :return: a map of reserve prices
    """
    dir_location = expt_directory + str(step) + '/'
    if not os.path.exists(dir_location):
        raise Exception(f'Directory {dir_location} does not exist.')
    config_file = configparser.ConfigParser()
    config_file.read(dir_location + '/config.ini')
    return read_reserve_prices_from_dict(config_file['RESERVE_PRICES'])


def get_gaussian(center: float, delta: float, epsilon: float, c_min: float = 0.0, c_max: float = 1.0) -> Gaussian:
    """
    Turns Hoeffding's like noise into gaussian noise.
    :param center:
    :param delta:
    :param epsilon:
    :param c_min:
    :param c_max:
    :return:
    """
    c0, c1, c2, c3 = c_min, center - epsilon, center + epsilon, c_max
    d = delta
    if c1 < c0:
        c1 = c0
    if c2 > c3:
        c2 = c3
    # assert c_min <= c1 <= c2 <= c_max, f'Cannot satisfy: {c_min} <= {c1} <= {c2} <= {c_max} for (c={center}, epsilon={epsilon})'
    if abs(c1 - c2) < 1e-10:
        return Gaussian(c1, 0.0)
    dc = (c1 - c0) ** 2 + (c3 - c2) ** 2
    if dc < 1e-10:
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


def get_gp_algorithm_param(which_algorithm, the_values, the_gaussians):
    the_alphas = 1e-10
    if which_algorithm == 'gp':
        the_ys = the_values
        the_noise = 1e-10
    elif which_algorithm == 'gpm':
        the_ys = [-g.mean for g in the_gaussians]
        the_noise = 1e-10
    elif which_algorithm == 'gpn':
        the_ys = [g.mean for g in the_gaussians]
        the_noise = 1e-10
        the_alphas = np.array([g.std ** 2 for g in the_gaussians])
    else:
        raise Exception(f'unknown algorithm {which_algorithm}')
    return the_ys, the_noise, the_alphas


def safe_create_dir(dir_location: str, fail_on_exists: bool = True) -> str:
    """
    Safely creates a directory
    :param dir_location:
    :param fail_on_exists:
    :return:
    """
    if not os.path.exists(dir_location):
        os.makedirs(dir_location)
    elif fail_on_exists:
        raise Exception(f'Directory {dir_location} already exists, stopping the experiment')
    return dir_location


def save_step_config_file(step: int, map_of_reserve_prices: Dict[Good, float], expt_directory: str, fail_on_exists: bool = True):
    """
    Saves a reserve price map to a config file
    :param step:
    :param map_of_reserve_prices:
    :param expt_directory:
    :param fail_on_exists:
    :return:
    """
    config_file = configparser.ConfigParser()
    config_file['RESERVE_PRICES'] = {g.id: r for g, r in map_of_reserve_prices.items()}
    dir_location = safe_create_dir(expt_directory + str(step) + '/', fail_on_exists)
    with open(dir_location + '/config.ini', 'w') as configfile:
        config_file.write(configfile)


def read_revenue(step: int, expt_directory: str) -> float:
    """
    Reads the revenue of a step of an experiment.
    :param step:
    :param expt_directory:
    :return:
    """
    with open(expt_directory + str(step) + '/eq.txt') as f:
        revenue = float(f.readline())
    return -revenue


def get_tuple_of_reserves(map_of_reserve: Dict[Good, float]) -> Tuple[float]:
    """
    This function guarantees that the reserve prices are given in the right order to the optimizer.
    :param map_of_reserve:
    :return:
    """
    return tuple(map_of_reserve[Good({s[0], s[1], s[2]}, None, None)] for s in ordered_segments)


def get_map_of_reserves(tuple_reserves: Tuple[float]) -> Dict[Good, float]:
    """
    Takes in a tuple of reserves and turns in into a dictionary.
    :param tuple_reserves:
    :return:
    """
    return_map = {}
    for i, s in enumerate(ordered_segments):
        return_map[Good({s[0], s[1], s[2]}, None, None)] = tuple_reserves[i]
    return return_map


def pretty_print_map_of_reserve(map_of_reserve: Dict[Good, float]) -> PrettyTable:
    """
    Takes in a map from good to reserve prices and returns a prettytable.
    :param map_of_reserve:
    :return:
    """
    reserve_table = PrettyTable()
    reserve_table.field_names = ['Market', 'Reserve']
    reserve_table.align['Market'] = 'l'
    reserve_table.align['Reserve'] = 'l'
    for g, r in map_of_reserve.items():
        reserve_table.add_row([g.id, r])
    return reserve_table
