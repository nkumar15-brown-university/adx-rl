from dataclasses import dataclass
from typing import Set, List, Dict

from prettytable import PrettyTable
import game.game as game


@dataclass
class Good:
    """
    Represents an impression opportunity
    """
    id: str
    market_segments: Set[str]
    supply: int
    reserve_price: float

    def __init__(self, name: Set[str], supply: int, reserve_price: float):
        self.market_segments = name
        self.supply = supply
        self.reserve_price = reserve_price
        list_of_segments = list(self.market_segments)
        list_of_segments.sort()
        self.id = "".join([x[0] for x in list_of_segments])
        # self.id = "".join(list_of_segments)

    def __repr__(self):
        return "(" + self.id + "," + str(self.supply) + "," + str(self.reserve_price) + ")"

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other):
        return self.supply <= other.supply

    def __eq__(self, other):
        return self.market_segments == other.market_segments

    def __matches__(self, other):
        return other.market_segments.issubset(self.market_segments)


@dataclass
class Campaign:
    """
    Represents a campaign
    """
    name: str
    reach: int
    budget: float
    spend: float ## How much has been spent so far on the campaign (e.g. via bids won)
    target: Good

    def __repr__(self):
        return "(" + self.name + ", " + self.target.id + ", " + str(self.reach) + ", " + str(self.budget) + ", " + str(self.budget / self.reach) + ")"

    def __lt__(self, other):
        return (self.budget / self.reach) <= (other.budget / other.reach)

    def __hash__(self):
        return hash(self.name)


@dataclass
class Market:
    """
    A market is a list of campaigns together with a list of goods
    """
    campaigns: List[Campaign]
    goods: List[Good] ## TODO: rename this to impression_opps
    campaigns_pmf: Dict[Campaign, float]
    impression_opps_pmf: Dict[Good, float]

    def __init__(self, campaigns_pmf: Dict[Campaign, float], impression_opps_pmf: Dict[Good, float]):
    	self.campaigns_pmf = campaigns_pmf
    	self.impression_opps_pmf = impression_opps_pmf

    def draw_campaigns(self, draw_amount: int, clear_current = True):
    	if clear_current:
    		self.campaigns = []
    	for i in range(draw_amount):
    		self.campaigns.append(game.draw_one(self.campaigns_pmf))

    def draw_impression_opps(self, draw_amount: int, clear_current = True):
    	if clear_current:
    		self.goods = []
    	for i in range(draw_amount):
    		self.goods.append(game.draw_one(self.impression_opps_pmf)) 

    def initialize(self, num_of_campaigns: int, num_of_impression_opps: int):
    	self.draw_campaigns(num_of_campaigns)
    	self.draw_impression_opps(num_of_impression_opps)
    	return self.campaigns, self.goods

    def run_auction(self, bids, update_campaigns = True):
    	allocations, expenditure = game.run_auctions(self.goods, self.impression_opps_pmf.keys(), self.campaigns, bids)
    	## allocations = {c: {g: 0 for g in goods} for c in campaigns}
    	## expenditure = {c: {g: 0 for g in goods} for c in campaigns}
    	if (update_campaigns):
    		for campaign in campaigns:
    			temp_allocs = allocations[campaign]
    			temp_exp = expenditure[campaign]
    			for imp_count in temp_allocs.values():
    				campaign.reach -= imp_count
    			for cost in temp_exp.values():
    				campaign.spend += cost

@dataclass
class Allocation:
    """
    An allocation is a mapping from campaigns to impressions (goods).
    """
    market: Market
    allocation: Dict[Campaign, Dict[Good, int]]
    total_allocation_campaign: Dict[Campaign, int]
    total_allocation_good: Dict[Good, int]

    def __init__(self, market: Market, allocation: Dict[Campaign, Dict[Good, int]]):
        self.market = market
        self.allocation = allocation
        self.total_allocation_campaign = {}
        self.total_allocation_good = {}

    def get_total_campaign_allocation(self, c: Campaign) -> int:
        if c not in self.total_allocation_campaign:
            self.total_allocation_campaign[c] = sum(self.allocation[c][g] for g in self.market.goods)
        return self.total_allocation_campaign[c]

    def get_total_good_allocation(self, g: Good) -> int:
        if g not in self.total_allocation_good:
            self.total_allocation_good[g] = sum(self.allocation[c][g] for c in self.market.campaigns)
        return self.total_allocation_good[g]

    def __str__(self):
        allocation_table = PrettyTable()
        allocation_table.field_names = ['Campaign'] + [g.id for g in self.market.goods]
        allocation_table.align['Campaign'] = "l"
        for c in self.allocation:
            allocation_table.add_row([c] + [self.allocation[c][g] for g in self.allocation[c]])
        # return allocation_str
        return allocation_table.__str__()


@dataclass
class Bid:
    """
    A bid of a campaign is for a good and specifics a bid amount and bid limit.
    """
    campaign: Campaign
    good: Good
    bid: float
    limit: float

    def __init__(self, campaign: Campaign, good: Good, bid: float, limit: float):
        self.campaign = campaign
        self.good = good
        self.bid = bid
        self.limit = limit
        # A bid cannot be negative
        assert self.bid >= 0
        # A limit cannot be non-positive
        assert self.limit > 0
        # A bid cannot be bigger than its limit, since in the worst case a bidder could en up paying a price arbitrarily close to its bid.
        assert self.limit >= self.bid

    def __repr__(self):
        return str(self.campaign) + " bid " + str(self.bid) + " for " + str(self.good) + " with limit " + str(self.limit)

    def __lt__(self, other):
        return self.bid <= other.bid


class Sorting:
    @staticmethod
    def copy_and_sort_goods(list_of_goods: List[Good]) -> List[Good]:
        copy_list = list_of_goods.copy()
        copy_list.sort(key=lambda g: (g.reserve_price, g.supply), reverse=True)
        return copy_list

    @staticmethod
    def copy_and_sort_campaigns(list_of_campaigns: List[Campaign]) -> List[Campaign]:
        copy_list = list_of_campaigns.copy()
        copy_list.sort(reverse=True)
        return copy_list


class PrettyPrints:
    @staticmethod
    def get_bids_pretty_table(list_of_bids: List[Bid]) -> PrettyTable:
        bids_table = PrettyTable()
        bids_table.field_names = ['Campaign', 'Good', 'Bid', 'Limit']
        bids_table.align['Campaign'] = "l"
        bids_table.align['Good'] = "l"
        for b in list_of_bids:
            bids_table.add_row([b.campaign, b.good, b.bid, b.limit])
        return bids_table

    @staticmethod
    def get_anonymous_prices_pretty_table(list_of_prices: Dict[Good, float]) -> PrettyTable:
        prices_table = PrettyTable()
        prices_table.field_names = ['Good', 'Price']
        for g, p in list_of_prices.items():
            prices_table.add_row([g, p])
        return prices_table

    @staticmethod
    def get_non_anonymous_prices_pretty_table(prices: Dict[Campaign, Dict[Good, float]]) -> PrettyTable:
        prices_table = PrettyTable()
        prices_table.field_names = ['Campaign', 'Good', 'Price']
        for c, g_p_map in prices.items():
            for g, p in g_p_map.items():
                prices_table.add_row([c.name, g, p])
        return prices_table

    @staticmethod
    def get_expenditure_pretty_table(expenditure: Dict[Campaign, Dict[Good, float]]) -> PrettyTable:
        expenditure_table = PrettyTable()
        expenditure_table.field_names = ['Campaign', 'Good', 'Expenditure']
        for c, g_e_map in expenditure.items():
            for g, e in g_e_map.items():
                expenditure_table.add_row([c.name, g, e])
        return expenditure_table
