from typing import List, Tuple, Dict

from game.structures import Campaign, Good, Market, Allocation, Bid, Sorting


def waterfall(m: Market) -> Tuple[Allocation, Dict[Campaign, Good]]:
    """
    Given a market, run the waterfall algorithm.
    :param m:
    :return:
    """
    # Book keeping structures
    alloca = {c: {g: 0 for g in m.goods} for c in m.campaigns}
    prices = {c: {g: g.reserve_price for g in m.goods} for c in m.campaigns}
    total_allocation = {c: 0 for c in m.campaigns}
    # Sort a shallow copy of campaigns to get the order of allocation
    list_of_ordered_campaigns = Sorting.copy_and_sort_campaigns(m.campaigns)
    # Keep track of the remaining supply
    remaining_supply = {g: g.supply for g in m.goods}

    # Allocate each campaign in order
    for c in list_of_ordered_campaigns:
        # Check if the campaign can be satisfied with the remaining supply
        if sum([remaining_supply[g] for g in m.goods if g.__matches__(c.target)]) >= c.reach:
            list_of_c_demanded_goods = list(filter(lambda g: g.__matches__(c.target), m.goods))
            second_highest = []
            for g in list_of_c_demanded_goods:
                # Get the competing campaigns, i.e., those that demand g. Filter bids that do not meet reserve and add an Auctioneer bid with the reserve price.
                list_of_competition = list(filter(lambda x: x.budget / x.reach >= g.reserve_price, [c for c in list_of_ordered_campaigns if g.__matches__(c.target)])) \
                                      + [Campaign("Auctioneer", 1, g.reserve_price, g)]
                # Order by descending order of bids
                list_of_competition = Sorting.copy_and_sort_campaigns(list_of_competition)
                # Compute the campaign that has the second highest bid. Note that this is always something, as the Auctioneer's bid is always there.
                campaign_with_2nd_high = list_of_competition[1] if len(list_of_competition) > 1 else list_of_competition[0]
                assert (campaign_with_2nd_high.budget / campaign_with_2nd_high.reach) >= 0
                second_highest += [(g, campaign_with_2nd_high)]
            # Sort the selected campaigns by ascending order of bids.
            second_highest.sort(key=lambda x: x[1], reverse=False)
            # Allocate greedily from all goods in ascending order of second_highest bid.
            for g, culpable_c in second_highest:
                # Allocate as much as needed
                alloca[c][g] = min(remaining_supply[g], c.reach - total_allocation[c])
                # If actual allocation happened, update the book keeping stuff.
                if alloca[c][g] > 0:
                    # Book keeping
                    remaining_supply[g] -= alloca[c][g]
                    total_allocation[c] += alloca[c][g]
                    prices[c][g] = culpable_c.budget / culpable_c.reach
            # If the allocated bundle is too expensive, give all the goods back.
            # This would have an effect as if the campaign was never there (only if ordering camp. by descending order of bids)
            if sum([alloca[c][g] * prices[c][g] for g in m.goods]) > c.budget:
                total_allocation[c] = 0
                for g in m.goods:
                    alloca[c][g] = 0
                    remaining_supply[g] += alloca[c][g]
                    prices[c][g] = g.reserve_price
    return Allocation(m, alloca), prices


def wf_strategy(market: Market) -> List[Bid]:
    # The wf strategy is to bid only on those goods for which the bidder was allocated.
    # The bid is (bid, limit) = (p_cg, p_cg x_cg) in case p_cg >0; otherwise the bid is (bid, limit) = (0.0, c.budget) in case p_g=0.
    wf_alloca, wf_prices = waterfall(market)
    return [Bid(c, g, wf_prices[c][g], wf_alloca.allocation[c][g] * wf_prices[c][g] if wf_prices[c][g] > 0 else c.budget)
            for c in market.campaigns for g in market.goods if wf_alloca.allocation[c][g] > 0]
