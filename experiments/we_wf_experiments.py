from game.structures import Market, Campaign, Good
from game.game import draw_one_impression_opportunity, run_auctions, draw_one_campaign
from strategies.WE import we_strategy
from strategies.WF import wf_strategy
from game.structures import PrettyPrints
from typing import List, Dict


def run_we_wf_experiments(reach_discount_factor: float,
                          k: int,
                          num_WE: int,
                          num_WF: int,
                          goods: List[Good],
                          pmf_base_goods: Dict[Good, float],
                          possible_campaign_targets: List[Good],
                          pmf_target_goods: Dict[Good, float], verbose=False):
    """
    Runs one WE, WF experiment with all the given parameters and returns the results, i.e., the utilities of players and the revenue of the auctioneer.
    :param reach_discount_factor:
    :param k:
    :param num_WE:
    :param num_WF:
    :param goods:
    :param pmf_base_goods:
    :param possible_campaign_targets:
    :param pmf_target_goods:
    :param verbose:
    :return:
    """
    # Draw random campaigns
    campaigns = [draw_one_campaign(num_WE + num_WF, reach_discount_factor, k, possible_campaign_targets, pmf_target_goods) for _ in range(0, num_WE + num_WF)]
    if verbose:
        print("\n*** Random Campaigns ***")
        for c in campaigns:
            print(c)

    assert num_WE + num_WF == len(campaigns)
    # -- Run Strategies
    market = Market(campaigns, goods)

    # WE strategy
    we_bids = we_strategy(market)
    if verbose:
        print("\n*** WE Bids ***")
        print(PrettyPrints.get_bids_pretty_table(we_bids))

    # WF strategy
    wf_bids = wf_strategy(market)
    if verbose:
        print("\n*** WF Bids ***")
        print(PrettyPrints.get_bids_pretty_table(wf_bids))

    # Computing the final bids depend on the strategy of each player.
    we_c = [campaigns[i] for i in range(0, num_WE)]
    wf_c = [campaigns[i] for i in range(num_WE, num_WE + num_WF)]
    final_we_bids = list(filter(lambda x, set_of_c=we_c: x.campaign in set_of_c, we_bids))
    final_wf_bids = list(filter(lambda x, set_of_c=wf_c: x.campaign in set_of_c, wf_bids))
    all_agents_bids = final_we_bids + final_wf_bids

    if verbose:
        print("\n*** Final Bids ***")
        print(PrettyPrints.get_bids_pretty_table(all_agents_bids))

    # -- Run auctions simulations and collect results
    if verbose:
        print("\n\n******* RUNNING AUCTIONS **********\n")
    # -- Impression Opportunities
    # Draw random impression opportunities
    impression_opportunities = [draw_one_impression_opportunity(pmf_base_goods) for _ in range(0, k)]
    # print("some_impression_opportunities = ", impression_opportunities)

    the_allocations, the_expenditure = run_auctions(impression_opportunities, goods, campaigns, all_agents_bids)
    return we_c, wf_c, the_allocations, the_expenditure
