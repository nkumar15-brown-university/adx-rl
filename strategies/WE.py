import itertools
from typing import Dict, List

import pulp

from game.structures import Market, Allocation, Good, Bid, Sorting


def greedy_allocation(m: Market) -> Allocation:
    """
    Given a market, returns a greedy allocation.
    :param m: a market
    :return: an Allocation
    """
    # Sort a shallow copy of campaigns to get the order of allocation
    list_of_ordered_campaigns = Sorting.copy_and_sort_campaigns(m.campaigns)
    # Sort a shallow copy of goods to get the order of allocation
    list_of_ordered_goods = Sorting.copy_and_sort_goods(m.goods)

    # Book keeping structures
    remaining_supply = {g: g.supply for g in m.goods}
    allocation = {c: {g: 0 for g in m.goods} for c in m.campaigns}
    total_allocation = {c: 0 for c in m.campaigns}
    # Loop through Campaigns
    for c in list_of_ordered_campaigns:
        # Check if there are enough goods to completely allocate the campaign.
        if sum([remaining_supply[g] for g in m.goods if g.__matches__(c.target)]) >= c.reach:
            # Loop through Goods.
            for g in list_of_ordered_goods:
                if g.__matches__(c.target):
                    allocation[c][g] = min(c.reach - total_allocation[c], remaining_supply[g])
                    total_allocation[c] = total_allocation[c] + allocation[c][g]
                    remaining_supply[g] = remaining_supply[g] - allocation[c][g]
                # If the goods are too expensive, give them back
            if sum([allocation[c][g] * g.reserve_price for g in list_of_ordered_goods]) > c.budget:
                total_allocation[c] = 0
                for g in list_of_ordered_goods:
                    allocation[c][g] = 0
                    remaining_supply[g] += allocation[c][g]

    return Allocation(m, allocation)


def pricing(allocation: Allocation) -> Dict[Good, float]:
    """
    Given an allocation, compute prices.
    :param allocation: an allocated market
    :return: a dictionary with prices, one per good
    """
    # Construct the Lp. We need a variable per good.
    prices_variables = pulp.LpVariable.dicts('prices', [g for g in allocation.market.goods], 0.0)
    indifference_slack_variables = pulp.LpVariable.dicts('slack', [(c, g1, g2) for c, g1, g2 in
                                                                   itertools.product(allocation.market.campaigns, allocation.market.goods, allocation.market.goods)], 0.0)

    model = pulp.LpProblem("Pricing", pulp.LpMaximize)
    # Maximum revenue objective, minimizing slack.
    model += sum([prices_variables[g] * allocation.get_total_good_allocation(g) for g in allocation.market.goods]
                 +
                 [-indifference_slack_var for _, indifference_slack_var in indifference_slack_variables.items()])

    # IR constraints.
    for j in allocation.market.campaigns:
        if allocation.get_total_campaign_allocation(j) > 0:
            model += sum([prices_variables[g] * allocation.allocation[j][g] for g in allocation.market.goods]) <= j.budget
    # Indifference condition, a.k.a. compact condition, relaxed with slacks
    for i in allocation.market.goods:
        # Reserve price constraints
        model += prices_variables[i] >= i.reserve_price
        for j in allocation.market.campaigns:
            if allocation.allocation[j][i] > 0:
                for k in allocation.market.goods:
                    if i != k and k.__matches__(j.target) and allocation.allocation[j][k] < k.supply:
                        model += prices_variables[i] <= prices_variables[k] + indifference_slack_variables[(j, i, k)]
    model.solve()
    # for _, indifference_slack_var in indifference_slack_variables.items():
    #    if indifference_slack_var.value() > 0 or True:
    #        print(indifference_slack_var.value())
    return {g: prices_variables[g].value() for g in allocation.market.goods}


def we_strategy(market: Market) -> List[Bid]:
    # The we strategy is to bid only on those goods for which the bidder was allocated.
    # The bid is (bid, limit) = (p_g, p_g x_cg) in case p_g >0; otherwise the bid is (bid, limit) = (0.0, c.budget) in case p_g=0.
    allocation_object = greedy_allocation(market)
    prices = pricing(allocation_object)
    return [Bid(c, g, prices[g], allocation_object.allocation[c][g] * prices[g] if prices[g] > 0 else c.budget)
            for c in market.campaigns for g in market.goods if allocation_object.allocation[c][g] > 0]
