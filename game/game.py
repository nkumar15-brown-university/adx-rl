import math
import uuid
from random import choice
from typing import List, Tuple, Dict

import numpy as np

from game.structures import Good, Bid, Campaign


def second_largest(bids) -> float:
    """
    Given a list of bids, returns the second largest. If there is only one bid, returns 0.0
    :param bids:
    :return:
    """
    count = 0
    m1 = m2 = float('-inf')
    for bid in bids:
        count += 1
        if bid.bid > m2:
            if bid.bid >= m1:
                m1, m2 = bid.bid, m1
            else:
                m2 = bid.bid
    return m2 if count >= 2 else 0.0


def draw_one_impression_opportunity(pmf_base_goods: Dict[Good, float]) -> Good:
    """
    Draw one good according to the given probability mass function
    :param pmf_base_goods:
    :return:
    """
    u = np.random.uniform(0, 1)
    accumulator = 0
    for g, prob in pmf_base_goods.items():
        accumulator += prob
        if u <= accumulator:
            return g


def draw_one_campaign(n: int, reach_discount_factor: float, k: int, goods: List[Good], pmf_target_goods: Dict[Good, float]):
    """
    Draw one random campaign according to the rules.
    :param n:
    :param reach_discount_factor:
    :param k:
    :param goods:
    :param pmf_target_goods:
    :return:
    """
    random_target = choice(goods)
    # ToDo: Unclear whether we should ceil or floor here. Ceil is to strict, floor is to lax.
    reach = math.ceil((reach_discount_factor * k * pmf_target_goods[random_target]) / n)
    if reach <= 0:
        raise Exception("A campaign cannot have a non-positive reach")
    # A normal random variable here means that, in theory, rewards could be unbounded. Our theory does not work in this case.
    # budget = np.random.normal(reach, 0.1 * reach)
    # The beta variable is bounded and with the above parameters, is a reasonable approximation to what we were looking for with the normal.
    budget = reach * (np.random.beta(10, 10) + 0.5)
    # The beta variable before was to symmetric perhaps resulting in a too easy to optimize revenue. Here we introduce some asymmetry
    # budget = reach * (np.random.beta(3, 10) + 0.5)
    if budget <= 0:
        raise Exception("A campaign cannot have a non-positive budget")
    return Campaign("Random Campaign " + str(uuid.uuid4()), reach, budget, random_target)


def run_auctions(impression_opportunities: List[Good], goods: List[Good], campaigns: List[Campaign], standing_bids: List[Bid]) -> \
        Tuple[Dict[Campaign, List[Good]], Dict[Campaign, List[Good]]]:
    allocations = {c: {g: 0 for g in goods} for c in campaigns}
    expenditure = {c: {g: 0 for g in goods} for c in campaigns}
    reserve_prices = {g: g.reserve_price for g in goods}
    # Run each individual second price auction.
    # print("\n\n --------- Running Auctions ------- \n \n")
    for i in impression_opportunities:
        # print("Auction of ", i)
        # print("\t standing_bids = ", standing_bids)
        # Collect relevant bids. These are all the bids that match the impression opportunity and are at least the reserve price.
        relevant_bids = list(filter(lambda bid, g=i, r=reserve_prices: g.__matches__(bid.good) and bid.bid >= r[g], standing_bids))
        if len(relevant_bids) > 0:
            # The bids might contain competing bids from the same agent. Pick only the max bid of each agent. We filter by agent (campaign), and take the max if it exists.
            relevant_bids = sum(list(map(lambda l: [max(l)] if len(l) > 0 else [], [list(filter(lambda x, a=c: a == x.campaign, relevant_bids)) for c in campaigns])), [])
            if len(relevant_bids) == 0:
                raise Exception("This should never occur.")
            # Get the winning bid
            max_bid = max(relevant_bids)
            # Get all the bids that are at least as big as the winning bids.
            winning_bids = list(filter(lambda b, win_bid_value=max_bid.bid: b.bid >= win_bid_value, relevant_bids))
            # Compute the price, which is defined as the max between the second largest of the relevant bids and the reserve.
            # Note the price of the second largest bid is zero if there is no such bid. Also, by this point all relevant bids can afford the reserve.
            price = max(second_largest(relevant_bids), reserve_prices[i])
            # Allocate impressions to winners, breaking ties randomly. First, select a random winner among all winners, then allocate and price.
            winner = choice(winning_bids)
            allocations[winner.campaign][i] += 1
            expenditure[winner.campaign][i] += price
            # Money has been potentially spent. Hence, remove all the bids that have reached their limit. A bid limit is the sum of expenditure over all matching markets.
            # We remove the bids where expenditure across all matching markets is less than the bid since we assume a bidder could always end up paying its bid (but not frenq).
            standing_bids = list(
                filter(lambda bid_obj: bid_obj.limit - sum([expenditure[bid_obj.campaign][g] for g in goods if g.__matches__(bid_obj.good)]) >= bid_obj.bid, standing_bids))
            # Some debug info
            # print("%%%% relevant_bids = ", relevant_bids)
            # print("\t\twinning_bids = ", winning_bids)
            # print("\t\t\t price = ", price)
            # print("\t\t\t\t winner is ", winner)
    return allocations, expenditure
