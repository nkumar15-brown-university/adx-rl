import math

from game.statistics import compute_sigmoidal_effective_reach_ratio
from game.structures import Good


class SingletonSetup:
    """
    An object that ties together all the information needed to run an experiment.
    """
    path_to_results = '../results/experiments/'

    class __SingletonSetup__:
        expt_step = None
        reserve_prices = None

        def __init__(self, expt_id: str, k: int, n: int, reach_discount_factor: float, eps: float, delta: float, budget: int):
            self.expt_id = expt_id
            # -- Common Parameters
            self.k = k
            self.n = n
            self.reach_discount_factor = reach_discount_factor
            self.eps = eps
            self.delta = delta
            self.budget = budget
            self.prob_max_market_segment = 4381.0 / 10000.0  # Corresponding to FL, self.possible_campaign_targets[15]: 4381.0 / 10000.0

            # Base Goods. These have meaningless supply and reserve prices of None, but we update with actual supply and reserve price next.
            self.base_goods = [Good({"Male", "Young", "High"}, None, None),
                               Good({"Male", "Young", "Low"}, None, None),
                               Good({"Male", "Old", "High"}, None, None),
                               Good({"Male", "Old", "Low"}, None, None),
                               Good({"Female", "Young", "High"}, None, None),
                               Good({"Female", "Young", "Low"}, None, None),
                               Good({"Female", "Old", "High"}, None, None),
                               Good({"Female", "Old", "Low"}, None, None)]
            # Impression opportunities probability mass function.
            self.pmf_base_goods = {self.base_goods[0]: 517.0 / 10000.0,
                                   self.base_goods[1]: 1836.0 / 10000.0,
                                   self.base_goods[2]: 808.0 / 10000.0,
                                   self.base_goods[3]: 1795.0 / 10000.0,
                                   self.base_goods[4]: 256.0 / 10000.0,
                                   self.base_goods[5]: 1980.0 / 10000.0,
                                   self.base_goods[6]: 407.0 / 10000.0,
                                   self.base_goods[7]: 2401.0 / 10000.0}
            # Compute the actual number of expected goods.
            for g in self.base_goods:
                # ToDo: unclear here whether we should use ceiling or floor. This should be coordinated with the way campaigns are generated.
                g.supply = math.ceil(self.k * self.pmf_base_goods[g])
            # -- Campaigns
            self.possible_campaign_targets = [Good({"Male", "Young", "High"}, None, None),
                                              Good({"Male", "Young", "Low"}, None, None),
                                              Good({"Male", "Old", "High"}, None, None),
                                              Good({"Male", "Old", "Low"}, None, None),
                                              Good({"Female", "Young", "High"}, None, None),
                                              Good({"Female", "Young", "Low"}, None, None),
                                              Good({"Female", "Old", "High"}, None, None),
                                              Good({"Female", "Old", "Low"}, None, None),
                                              Good({"Male", "Young"}, None, None),
                                              Good({"Male", "Old"}, None, None),
                                              Good({"Male", "High"}, None, None),
                                              Good({"Male", "Low"}, None, None),
                                              Good({"Female", "Young"}, None, None),
                                              Good({"Female", "Old"}, None, None),
                                              Good({"Female", "High"}, None, None),
                                              Good({"Female", "Low"}, None, None),
                                              Good({"Young", "Low"}, None, None),
                                              Good({"Young", "High"}, None, None),
                                              Good({"Old", "Low"}, None, None),
                                              Good({"Old", "High"}, None, None)]
            # Impression opportunities probability mass function.
            self.pmf_target_goods = {self.possible_campaign_targets[0]: 517.0 / 10000.0,
                                     self.possible_campaign_targets[1]: 1836.0 / 10000.0,
                                     self.possible_campaign_targets[2]: 808.0 / 10000.0,
                                     self.possible_campaign_targets[3]: 1795.0 / 10000.0,
                                     self.possible_campaign_targets[4]: 256.0 / 10000.0,
                                     self.possible_campaign_targets[5]: 1980.0 / 10000.0,
                                     self.possible_campaign_targets[6]: 407.0 / 10000.0,
                                     self.possible_campaign_targets[7]: 2401.0 / 10000.0,
                                     self.possible_campaign_targets[8]: 2353.0 / 10000.0,
                                     self.possible_campaign_targets[9]: 2603.0 / 10000.0,
                                     self.possible_campaign_targets[10]: 1325.0 / 10000.0,
                                     self.possible_campaign_targets[11]: 3631.0 / 10000.0,
                                     self.possible_campaign_targets[12]: 2236.0 / 10000.0,
                                     self.possible_campaign_targets[13]: 2808.0 / 10000.0,
                                     self.possible_campaign_targets[14]: 663.0 / 10000.0,
                                     self.possible_campaign_targets[15]: 4381.0 / 10000.0,
                                     self.possible_campaign_targets[16]: 3816.0 / 10000.0,
                                     self.possible_campaign_targets[17]: 773.0 / 10000.0,
                                     self.possible_campaign_targets[18]: 4196.0 / 10000.0,
                                     self.possible_campaign_targets[19]: 1215.0 / 10000.0}

        def update_expt_step(self, expt_step: int):
            self.expt_step = expt_step

        def update_reserve_prices(self, reserve_prices: float):
            self.reserve_prices = reserve_prices
            # Update the reserve prices
            for g in self.base_goods:
                g.reserve_price = self.reserve_prices[g]

    instance = None

    def __init__(self, expt_id: str, k: int, n: int, reach_discount_factor: float, eps: float, delta: float, budget: int):
        if not SingletonSetup.instance:
            SingletonSetup.instance = SingletonSetup.__SingletonSetup__(expt_id, k, n, reach_discount_factor, eps, delta, budget)

    @staticmethod
    def set_expt_step(expt_step: int):
        SingletonSetup.instance.update_expt_step(expt_step)

    @staticmethod
    def set_reserve_prices(reserve_prices: float):
        SingletonSetup.instance.update_reserve_prices(reserve_prices)

    @staticmethod
    def get_path_to_expt_step():
        return SingletonSetup.path_to_results + 'experiment_' + SingletonSetup.instance.expt_id + '/' + str(SingletonSetup.instance.expt_step) + '/'

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def number_of_samples_per_profile(self):
        return math.ceil(0.5 * ((1.0 / math.pow(self.eps, 2.0)) * math.log((4 * (self.n + 1) * self.budget) / self.delta)))

    def get_total_number_of_samples(self):
        return self.number_of_samples_per_profile() * (self.n + 1) * self.budget

    def compute_bounds_utility(self):
        reach = math.ceil((self.reach_discount_factor * self.k * self.prob_max_market_segment) / self.n)  # The way I have been defining reach so far.
        budget = reach * 1.5  # This is the case where the beta distribution is exactly 1.5 (very unlikely but in theory possible)
        max_utility = budget * compute_sigmoidal_effective_reach_ratio(self.k, reach)  # The campaign gets all its budget for free
        return max_utility

    def compute_bounds_revenue(self):
        pass

    def total_simulation_time(self, sec_per_simulation):
        return self.get_total_number_of_samples() * sec_per_simulation
