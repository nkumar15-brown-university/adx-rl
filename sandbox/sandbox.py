from datetime import datetime, timedelta
from game.structures import Good
from experiments.singletonsetup import SingletonSetup
import math
import numpy as np
import matplotlib.pyplot as plt

reserve_prices = {Good({"Male", "Young", "High"}, None, None): None,
                  Good({"Male", "Young", "Low"}, None, None): None,
                  Good({"Male", "Old", "High"}, None, None): None,
                  Good({"Male", "Old", "Low"}, None, None): None,
                  Good({"Female", "Young", "High"}, None, None): None,
                  Good({"Female", "Young", "Low"}, None, None): None,
                  Good({"Female", "Old", "High"}, None, None): None,
                  Good({"Female", "Old", "Low"}, None, None): None}

my_setup = SingletonSetup(expt_id=-1,
                          expt_step=-1,
                          single_reserve_price=reserve_prices,
                          k=1000,
                          n=8,
                          reach_discount_factor=1.0,
                          eps=0.1,
                          delta=0.1,
                          budget=5)
print("max_u = ", my_setup.compute_bounds_utility())
print("m = ", my_setup.number_of_samples_per_profile())
print("total_num_samples = ", my_setup.get_total_number_of_samples())
# with 10000 impressions
# sec_per_simulation = 0.78717914277857
# with 1000 impressions
# sec_per_simulation = 0.2819577563892711
# with 100 impressions
sec_per_simulation = 0.21558791531456842
# sec_per_simulation = 1
total_simulation_time = my_setup.total_simulation_time(sec_per_simulation)

d = datetime(1, 1, 1) + timedelta(seconds=total_simulation_time)
print("seconds = ", total_simulation_time)
print("D \t H \t M \t S")
print("%d \t %d \t %d \t %d" % (d.day - 1, d.hour, d.minute, d.second))

from skopt import gp_minimize
from experiments.plot_bo import plot_bo


def g(x):
    return (x - 0.5) * (x - 1.5)


def f(x):
    if x[0] == 1.2129553205232273:
        return g(x[0])
    elif x[0] == 0.5989098936152988:
        return g(x[0])
    elif x[0] == 1.2175355200388458:
        return g(x[0])
    else:
        raise Exception("Function not defined at x = ", x)


x0 = [[1.2129553205232273], [0.5989098936152988], [1.2175355200388458]]
y0 = [f(x) for x in x0]
result, optimizer = gp_minimize(func=f,
                                dimensions=[(0.5, 1.5)],
                                n_calls=0,
                                x0=x0,
                                y0=y0,
                                n_random_starts=0,
                                random_state=123)
print("result = ", result)
print("next point = ", optimizer.ask())
# plot_bo(lambda x: (x[0] - 0.5) * (x[0] - 1.5), 3, res, 0.0)
