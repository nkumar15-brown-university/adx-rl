import math
from typing import Dict

from game.structures import Campaign, Good


def compute_sigmoidal_effective_reach_ratio(x, reach):
    """
    Given a number of procurred impressions, computes a sigmoidal fraction of the reach.
    :param x:
    :param reach:
    :return:
    """
    return (2 / 4.08577) * (math.atan(4.08577 * (x / reach) - 3.08577) - math.atan(-3.08577))


def compute_statistics(allocations: Dict[Campaign, Dict[Good, int]], expenditure: Dict[Campaign, Dict[Good, float]]):
    """
    Computes the statistics of the game.
    :param allocations:
    :param expenditure:
    :return:
    """
    total_allocations = 0
    total_expenditure = 0
    total_effective_allocation = {}
    sigmoidal_effective_reach_ratio = {}
    utilities = {}
    for c, _ in allocations.items():
        total_c_allocations = sum([a for g, a in allocations[c].items()])
        total_c_expenditure = sum([a for g, a in expenditure[c].items()])
        total_allocations += total_c_allocations
        total_expenditure += total_c_expenditure
        if c not in total_effective_allocation:
            # The total effective allocation is the sum of the allocation across all market segments that match the campaign's target.
            total_effective_allocation[c] = sum([a if g.__matches__(c.target) else 0 for g, a in allocations[c].items()])
        else:
            raise Exception("1) This should NOT happen!")
        if c not in sigmoidal_effective_reach_ratio:
            # The sigmoidal effective reach ratio is compute with respect to the total effective allocation.
            sigmoidal_effective_reach_ratio[c] = compute_sigmoidal_effective_reach_ratio(total_effective_allocation[c], c.reach)
        else:
            raise Exception("2) This should NOT happen!")
        if c not in utilities:
            # The actual final utility.
            # print("Computing utilities:")
            # print("\t ", sigmoidal_effective_reach_ratio[c])
            # print("\t ", c.budget)
            # print("\t ", total_c_expenditure)
            utilities[c] = sigmoidal_effective_reach_ratio[c] * c.budget - total_c_expenditure
        else:
            raise Exception("3) This should NOT happen!")
    return utilities, total_expenditure
