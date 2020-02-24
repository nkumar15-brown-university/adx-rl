from dataclasses import dataclass
from typing import Set, List, Dict, OrderedDict
import uuid

from prettytable import PrettyTable
import game.game as game



@dataclass
class MarketSegment:
    """
    Represents a market segment
    """
    uid: int
    demographics: Set[str]

    def __init__(self, demographics: Set[str]):
        self.uid = uuid.uuid4().int
        self.demographics = demographics

    def __eq__(self, other):
        return self.demographics == other.demographics

    def __matches__(self, other):
        return other.demographics.issubset(self.demographics)

@dataclass
class Good:
    """
    Represents an impression opportunity
    """
    uid: int
    #id: str
    market_segment: MarketSegment
    supply: int ## TODO: what is this?
    reserve_price: float ## TODO: what is this?

    def __init__(self, market_segment: MarketSegment, supply: int, reserve_price: float):
        self.uid = uuid.uuid4().int
        self.market_segment = market_segment
        self.supply = supply
        self.reserve_price = reserve_price   
        #list_of_segments = list(self.market_segments)
        #list_of_segments.sort()
        #self.id = "".join([x[0] for x in list_of_segments])
        # self.id = "".join(list_of_segments)

    def __repr__(self):
        return "(" + self.uid + "," + str(self.supply) + "," + str(self.reserve_price) + ")"

    def __hash__(self):
        return hash(self.uid)

    def __lt__(self, other):
        return self.supply <= other.supply

    def __eq__(self, other):
        return self.market_segment == other.market_segment ## TODO: should equality be by uid or by market segment?

    def __matches__(self, other):
        return self.market_segment.__matches__(other.market_segment)


@dataclass
class Campaign:
    """
    Represents a campaign
    """
    uid: int
    reach: int
    budget: float
    spend: float ## How much has been spent so far on the campaign (e.g. via bids won)
    remaining_reach: int ## How much of the reach is left
    target: MarketSegment ## Which market segment to target

    def __init__(self, reach, budget, target):
        self.uid = uuid.uuid4().int
        self.reach = reach
        self.budget = budget
        self.spend = 0.0
        self.remaining_reach = reach
        self.target = target

    def __repr__(self):
        return "(" + str(self.uid) + ", " + str(self.target) + ", " + str(self.reach) + ", " + str(self.budget) + ", " + str(self.budget / self.reach) + ")"

    def __lt__(self, other):
        return (self.budget / self.reach) <= (other.budget / other.reach)

    def __hash__(self):
        return hash(self.uid)

    def to_vector(campaign: Campaign):
        return []

    def from_vector(campaign_vector: List, all_possible_market_segments: Set[MarketSegment]):
        camp = Campaign(-1, -1.0, None)
        return camp


@dataclass
class Market:
    """
    A market is a list of campaigns together with a list of goods
    """
    campaigns: List[Campaign]
    goods: List[Good] ## TODO: rename this to impression_opps
    campaigns_pmf: OrderedDict[List[T], float]
    market_segments_pmf: Dict[MarketSegment, float]

    def __init__(self, campaigns_pmf: OrderedDict[List[T], float], market_segments_pmf: OrderedDict[MarketSegment, float]):
    	self.campaigns_pmf = campaigns_pmf
    	self.market_segments_pmf = market_segments_pmf

    def draw_campaigns(self, draw_amount: int, clear_current = True):
    	if clear_current:
    		self.campaigns = []
    	for i in range(draw_amount):
            campaign_specification = game.draw_one(self.campaigns_pmf)
            camp = Campaign(reach, budget, )
    		self.campaigns.append(camp)

    def draw_impression_opps(self, draw_amount: int, clear_current = True):
    	if clear_current:
    		self.goods = []
    	for i in range(draw_amount):
            imp_opp = Good(game.draw_one(self.market_segments_pmf), 1, 0.0)
    		self.goods.append(imp_opp)

    def initialize(self, num_of_campaigns: int, num_of_impression_opps: int):
    	self.draw_campaigns(num_of_campaigns)
    	self.draw_impression_opps(num_of_impression_opps)
    	return self.campaigns, self.goods

    def run_auction(self, bids, update_campaigns = True):
    	allocations, expenditure = game.run_auctions(self.goods, self.market_segments_pmf.keys(), self.campaigns, bids) ## TODO: this is broken now
    	## allocations = {c: {g: 0 for g in goods} for c in campaigns}
    	## expenditure = {c: {g: 0 for g in goods} for c in campaigns}
    	if (update_campaigns):
    		for campaign in campaigns:
    			temp_allocs = allocations[campaign]
    			temp_exp = expenditure[campaign]
    			for imp_count in temp_allocs.values():
    				campaign.remaining_reach -= imp_count
    			for cost in temp_exp.values():
    				campaign.spend += cost
    	return allocations, expenditure


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
    A bid of a campaign is for a market segment and specifics a bid amount and bid limit.
    """
    campaign: Campaign
    market_segment: MarketSegment
    bid: float
    limit: float

    def __init__(self, campaign: Campaign, market_segment: MarketSegment, bid: float, limit: float):
        self.campaign = campaign
        self.market_segment = market_segment
        self.bid = bid
        self.limit = limit
        # A bid cannot be negative
        assert self.bid >= 0
        # A limit cannot be non-positive
        assert self.limit > 0
        # A bid cannot be bigger than its limit, since in the worst case a bidder could end up paying a price arbitrarily close to its bid.
        assert self.limit >= self.bid

    def __repr__(self):
        return str(self.campaign) + " bid " + str(self.bid) + " for " + str(self.market_segment) + " with limit " + str(self.limit)

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
