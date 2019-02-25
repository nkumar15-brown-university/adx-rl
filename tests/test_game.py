from game.structures import Campaign, Good, Market, Bid, PrettyPrints, Sorting, Allocation
from strategies.WE import greedy_allocation, pricing, we_strategy
from strategies.WF import waterfall, wf_strategy
from game.game import run_auctions, draw_one_impression_opportunity
from game.statistics import compute_statistics, compute_sigmoidal_effective_reach_ratio
from gt.brg import compute_eps_brg
import networkx as nx
import matplotlib.pyplot as plt
import math
import itertools


class TestGreedyAllocation():

    @staticmethod
    def get_market_1():
        if False:
            g1 = Good({"Male", "Young", "High"}, 149, 0.0)
            g2 = Good({"Male", "Young"}, 25, 0.0)
            g3 = Good({"Male"}, 50, 0.0)
            g4 = Good({"Female"}, 200, 0.0)
        else:
            g1 = Good({"Male", "Young", "High"}, 149, 0.1)
            # g2 = Good({"Male", "Young"}, 25, 1.305)
            g2 = Good({"Male", "Young"}, 25, 1.4)
            g3 = Good({"Male"}, 50, 1.0)
            g4 = Good({"Female"}, 200, 0.5)

        c1 = Campaign("C1", 100, 123.5, Good({"Male"}, -1, -1))
        c2 = Campaign("C2", 100, 130.5, Good({"Male", "Young"}, -1, -1))
        c3 = Campaign("C3", 25, 130.5, Good({"Female"}, -1, -1))

        assert not (g3.__matches__(c2.target))

        """
        list_of_c = [c1, c2, c3]
        list_of_g = [g1, g2, g3, g4]
        for c in list_of_c:
            print(c)
            for g in list_of_g:
                print("\t", g, g.__matches__(c.target))
        """

        return Market([c1, c2, c3], [g1, g2, g3, g4])

    def test_greedy_allocation(self):
        m = TestGreedyAllocation.get_market_1()
        allocation = greedy_allocation(m)
        print("\n*** Greedy Alloc ***")
        print(allocation)

        # assert allocation.allocation[m.campaigns[0]][m.goods[0]] == 50
        # Check that we never allocate more than needed or more than exists
        for c in m.campaigns:
            assert allocation.get_total_campaign_allocation(c) == 0 or c.reach
        for g in m.goods:
            assert allocation.get_total_good_allocation(g) <= g.supply
        return allocation

    def test_greedy_allocation_1(self):
        g1 = Good({"Male", "Young", "High"}, 200, 1.0)
        c1 = Campaign("C1", 50, 100.0, Good({"Male"}, -1, -1))
        c2 = Campaign("C2", 99, 100.0, Good({"Male"}, -1, -1))
        m = Market([c1, c2], [g1])
        allocation = greedy_allocation(m)
        print(allocation)

    def test_pricing_algo(self):
        allocation = self.test_greedy_allocation()
        prices = pricing(allocation)
        import pulp
        c = allocation.market.campaigns
        g = allocation.market.goods
        l = [(c, g1, g2) for c, g1, g2 in itertools.product(c, g, g)]
        print("len(l) = ", len(l))
        print("l = ", l)
        indifference_slack_variables = pulp.LpVariable.dicts('slack', [(c, g1, g2) for c, g1, g2 in itertools.product(c, g, g)])
        print(c[0], g[0])
        print(indifference_slack_variables[(c[0], g[0], g[0])])

        # Check that all the prices are non-negative
        for g in allocation.market.goods:
            assert prices[g] >= 0.0
        print("\n*** WE Prices ***")
        print(PrettyPrints.get_anonymous_prices_pretty_table(prices))

        bids = we_strategy(allocation.market)
        print("\n*** WE Strategy ***")
        print(PrettyPrints.get_bids_pretty_table(bids))

    def test_wf(self):
        some_goods = [Good({"Male"}, 10, 0.0),
                      Good({"Female", "Young"}, 100, 0.0),
                      Good({"Female", "Young", "High"}, 20, 0.0)]

        c0 = Campaign("Agent 0", 9, 100.0, Good({"Male"}, -99, -1))
        c1 = Campaign("Agent 1", 10, 100.0, Good({"Male"}, -99, -1))
        c2 = Campaign("Agent 2", 30, 300.0, Good({"Female"}, -99, -1))
        c3 = Campaign("Agent 3", 41, 400.0, Good({"Female"}, -99, -1))
        c4 = Campaign("Agent 4", 1, 400.0, Good({"Female", "Young"}, -99, -1))
        c5 = Campaign("Agent 5", 39, 399.0, Good({"Female", "Young", "High"}, -99, -1))
        some_campaigns = [c0, c1, c2, c3, c4, c5]
        print(Good("Female", None, None).__matches__(c4.target))
        m = Market(some_campaigns, some_goods)

        # m = TestGreedyAllocation.get_market_1()
        # Compute the waterfall outcome.
        alloc, prices = waterfall(m)
        print("\n*** WF Allocation ***")
        print(alloc)

        print("\n*** WF Prices ***")
        print(PrettyPrints.get_non_anonymous_prices_pretty_table(prices))

        # Compute the waterfall strategy
        final_wf_strat = wf_strategy(m)
        print(PrettyPrints.get_bids_pretty_table(final_wf_strat))

    def test_draw_impression_opportunities(self):
        # Just making sure the distribution is correctly implemented.
        # counts = {g: 0 for g in goods}
        # for i in impression_opportunities:
        #    counts[i] += 1

        # for g, count in counts.items():
        #    print("count = ", g, "\t", count / k)
        pass

    def test_run_auctions(self):
        print("\t ****** \t")
        impression_opportunities = [Good({"M", "Y", "H"}, -11, -1),
                                    Good({"M", "O", "H"}, -12, -1),
                                    Good({"F", "Y", "H"}, -13, -1),
                                    Good({"F", "Y", "H"}, -14, -1)]
        print("impression_opportunities = ", impression_opportunities)
        goods = [Good({"M", "Y", "H"}, -10, 25.00),
                 Good({"M", "O", "H"}, -10, 1.00),
                 Good({"F", "Y", "H"}, -10, math.inf)]
        print("goods = ", goods)
        campaigns = [Campaign("Agent 1", 10, 100.0, goods[0]),
                     Campaign("Agent 2", 10, 100.0, goods[1])]
        print("campaigns = ", campaigns)
        all_agents_bids = [Bid(campaigns[0], Good({"M"}, -90, -1), 1.0, 1.249),
                           Bid(campaigns[0], Good({"F", "H"}, -91, -1), 1, 50.0),
                           Bid(campaigns[1], Good({"F"}, -92, -1), 9, 80.5),
                           Bid(campaigns[1], Good({"F"}, -93, -1), 100, 800.0)]

        allocations, expenditure = run_auctions(impression_opportunities, goods, campaigns, all_agents_bids)
        print("bids = ", PrettyPrints.get_bids_pretty_table(all_agents_bids))
        print("allocations = ", Allocation(Market(campaigns, goods), allocations))
        print("expenditure = ", PrettyPrints.get_expenditure_pretty_table(expenditure))

    def test_game(self):
        # -- Common Parameters
        # Base Goods. These have meaningless supply, we just use them to identify the type of goods in the auction.
        some_goods = [Good({"Male"}, -1, -1), Good({"Female"}, -1, -1)]
        # Number of impression opportunities
        k = 1000
        # Impression opportunities probability mass function.
        probability_mass_good = {some_goods[0]: 7.0 / 8.0, some_goods[1]: 1.0 / 8.0}
        for g in some_goods:
            # ToDo: unclear here whether we should use ceiling or floor. This should be coordinated with the way campaigns are generated.
            g.supply = math.ceil(k * probability_mass_good[g])
        # -- Campaigns
        c1 = Campaign("Agent 1", 10, 100.0, some_goods[0])
        c2 = Campaign("Agent 2", 30, 300.0, some_goods[1])
        c3 = Campaign("Agent 3", 40, 400.0, some_goods[1])
        some_campaigns = [c1, c2, c3]

        # -- Run Strategies
        # WE strategy
        we_bids = we_strategy(Market(some_campaigns, some_goods))
        print("we_bids = ", we_bids)
        # Synthetic bids of all agents. The assumption is that each agent has a single campaign.
        some_all_agents_bids = [Bid(c1, some_goods[0], 1 / 3, 1 / 3), Bid(c1, some_goods[1], 1 / 3, 4343),
                                Bid(c2, some_goods[0], 1 / 3, 1 / 3), Bid(c2, some_goods[1], 2 / 3, 2 / 3),
                                Bid(c3, some_goods[0], 1 / 3, 1 / 3)]
        # print(some_all_agents_bids)
        # some_all_agents_bids = we_bids

        # -- Impression Opportunities
        # Draw random impression opportunities
        some_impression_opportunities = [draw_one_impression_opportunity(probability_mass_good) for _ in range(0, k)]
        print("some_impression_opportunities = ", some_impression_opportunities)

        # -- Run auctions simulations and collect results
        the_allocations, the_expenditure = run_auctions(some_impression_opportunities, some_goods, some_campaigns, some_all_agents_bids)
        print("*** Final Allocations ***")
        for c, m in the_allocations.items():
            print(c)
            for g, a in m.items():
                print("\t", g, a)
        print("*** Final Expenses ***")
        for c, m in the_expenditure.items():
            print(c)
            for g, a in m.items():
                print("\t", g, a)

        print("*** Final Utilities ***")
        utilities, total_expenditure = compute_statistics(the_allocations, the_expenditure)
        for c, u in utilities.items():
            print(c, u)
        print("Total auctioneer revenue = ", total_expenditure)

    def test_statistics(self):
        grid = [i for i in range(0, 200)]
        sigmoidal = [compute_sigmoidal_effective_reach_ratio(i, 100) for i in grid]
        print(sigmoidal)
        plt.plot(grid, sigmoidal)
        plt.show()

    def test_double_ordering(self):

        g1 = Good({"Male", "Young", "High"}, 149, 1.0)
        g2 = Good({"Male", "Young"}, 25, 1.0)
        g3 = Good({"Male"}, 500, 1.0)
        g4 = Good({"Female"}, 200, 1.0)

        c1 = Campaign("C1", 100, 123.5, Good({"Male"}, -1, -1))
        c2 = Campaign("C2", 100, 130.5, Good({"Male", "Young"}, -1, -1))
        c3 = Campaign("C3", 25, 130.5, Good({"Female"}, -1, -1))

        market = Market([c1, c2, c3], [g1, g2, g3, g4])
        print(market.goods)
        ordered_goods = Sorting.copy_and_sort_goods(market.goods)
        print(ordered_goods)

        print(market.campaigns)
        ordered_campaigns = Sorting.copy_and_sort_campaigns(market.campaigns)
        print(ordered_campaigns)

    def test_new_wf(self):
        market = TestGreedyAllocation.get_market_1()
        allocation, prices = waterfall(market)
        print(allocation)
        print(PrettyPrints.get_non_anonymous_prices_pretty_table(prices))

        print(PrettyPrints.get_bids_pretty_table(wf_strategy(market)))

    def test_sink(self):
        G = nx.DiGraph()
        G.add_nodes_from([1, 2, 3])
        G.add_edge(1, 2)
        G.add_edge(2, 1)
        revenue = {1: 1, 2: 2, 3: 30}
        l = get_sinks(G, revenue)

    def test_new_sink(self):
        results_file = "../results/experiments/revenue_expt/grid_revenue/80/results.csv"
        sinks, revenue_per_node_per_sink, minimum_revenue_per_sink, worst_case_revenue = compute_eps_brg(file=results_file, eps=0.05)
        for scc in sinks:
            print("\n", scc)
        print(revenue_per_node_per_sink)
        print(minimum_revenue_per_sink)
        print(worst_case_revenue)
