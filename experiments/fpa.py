import math

import numpy as np


def compute_m(delta, eps, num_bidders):
    """
    Given delta, eps, and number of bidders, return the number of samples.
    :param delta:
    :param eps:
    :param num_bidders:
    :return:
    """
    return (math.log((2 * num_bidders) / delta)) / (2 * eps * eps)


def compute_eps_fpa(delta, m, num_bidders):
    """
    Given delta tolerance and the number of samples, compute the tolerance, eps, of the estimation.
    :param delta:
    :param m:
    :param num_bidders:
    :return:
    """
    return math.sqrt(math.log((2.0 * num_bidders) / delta) / (2.0 * m))


def expected_revenue_uniform_case(r, n):
    """
    This function implements the expected revenue of the auctioneer, at equilibrium, for a first price auction as a function of '
    reserve price r and the number of bidders n. The assumption is that bidders draw their values from a uniform distribution [0, 1],
    and play at equilibrium (Bayes-Nash eq).
    :param r: reserve price
    :param n: number of bidders
    :return: the expected revenue of a first-price auction, with reserve, where bidders play @ equilibrium and draw values from a continuous [0, 1] distribution.
    """
    return n * (math.pow(r, n) * (1 - r) + (n - 1) * (((1 / n) - (1 / (n + 1))) - ((math.pow(r, n) / n) - (math.pow(r, n + 1) / (n + 1)))))


def expected_revenue_exponential_case(r, n, l):
    """
    Case of exponentially distributed bidders.
    :param r:
    :param n:
    :return:
    """
    n = 2  # I don't have other n's here yet

    return 2.0 * r * math.exp(-l * r) + (((1 - 2.0 * l * r) * (math.exp(-2.0 * l * r))) / (2 * l))


def compute_strategy_uniform_case(r, v, n):
    """
    Compute the Bayes-Nash equilibria strategy for a first-price auction with reserve where bidders valuations are uniform [0,1].
    :param r:
    :param v:
    :param n:
    :return:
    """
    return 0.0 if r > v else (math.pow(r, n) / math.pow(v, n - 1.0)) + (((n - 1.0) / n) * (1.0 / math.pow(v, n - 1.0)) * (math.pow(v, n) - math.pow(r, n)))


def compute_strategy_exponential_case(r, v, n, l):
    """
    Compute the Bayes-Nash equilibria strategy for a first-price auction with reserve where bidders valuations are exponentially distributed with parameter l.
    :param r:
    :param v:
    :param n: Only works for n=2 at the moment.
    :param l:
    :return:
    """
    return 0.0 if r > v else ((l * r + math.exp(-l * r) - (l * v + 1) * math.exp(-l * v)) / (l * (1 - math.exp(-l * v))))


def get_revenue(profile_s, r):
    """
    Get the revenue of a first price auction with reserve.
    :param profile_s:
    :param r:
    :return:
    """
    sorted_v = np.sort(profile_s)
    return sorted_v[-1] if sorted_v[-1] >= r else 0


def expensive_function(valuations_sampler, strategies, expected_revenue, reserve_price, number_of_samples, number_of_players, eps):
    """
    For a given way of computing strategies (symmetrically for all players), a given reserve price, a given number of samples, and a gien number of players;
    return an \eps-estimate of the revenue that holds with probability 1 - \delta.
    This is the expensive function we are going to optimize through Bayesian Optimization and Uniform Sampling.
    :param valuations_sampler:
    :param strategies:
    :param expected_revenue:
    :param reserve_price:
    :param number_of_samples:
    :param number_of_players:
    :param eps:
    :return:
    """
    # reserve_price = reserve_price[0]  # The package for Bayesian Optimization uses a list to query the function.
    acumulator = 0.0
    for t in range(0, number_of_samples):
        v_profile = valuations_sampler(number_of_players)
        s_profile = [strategies(reserve_price, v, number_of_players) for v in v_profile]
        acumulator += get_revenue(s_profile, reserve_price)
    empirical_revenue = float(acumulator / number_of_samples)
    # if abs(empirical_revenue - expected_revenue(reserve_price, number_of_players)) > eps:
    #    raise Exception("Wrong estimate: ", abs(empirical_revenue - expected_revenue(reserve_price, number_of_players)), " > ", eps)
    return -1.0 * empirical_revenue


def uniform_search(the_f, bounds, budget):
    """
    Uniform search. Search f for the best parameter by uniform sampling a budget number of times.
    :param the_f:
    :param bounds:
    :param budget:
    :return:
    """
    x_iter = []
    evaluations = []
    best_eval_per_iter = [math.inf]
    for i in range(0, budget):
        x_iter += [np.random.uniform(bounds[0][0], bounds[0][1], 1)]
        evaluations += [the_f(x_iter[i])]
        best_eval_per_iter += [min(evaluations)]

    return x_iter, evaluations, best_eval_per_iter[1:]


def f(val_sampler, s, expected_revenue_f, m, n, eps):
    """
    Return the function that is going to be optimized via Bayesian Optimization.
    :param val_sampler:
    :param s:
    :param expected_revenue_f:
    :param m:
    :param n:
    :param eps:
    :return:
    """

    def inner_f(r):
        return expensive_function(val_sampler, s, expected_revenue_f, r, m, n, eps)

    return inner_f
