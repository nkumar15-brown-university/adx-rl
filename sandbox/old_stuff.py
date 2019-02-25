def check_no_outgoing_edges(component: nx.Graph, G: nx.Graph) -> bool:
    """
    Given a connected component of a graph, returns true if it has outgoing edges, and false otherwise.
    :param component:
    :param G:
    :return:
    """
    for node in component.nodes():
        out_edges = G.out_edges(node)
        for coming, going in out_edges:
            if going not in component.nodes:
                return False
    return True


def get_sinks(G: nx.Graph) -> List[List[str]]:
    """
    Given a graph, returns the sinks.
    :param G:
    :return:
    """
    # Compute strongly connected components.
    strong_components = nx.strongly_connected_component_subgraphs(G)
    # A sink is a strongly connected component of G that has no outgoing edges.
    sinks = list(filter(lambda X, base_graph=G: check_no_outgoing_edges(X, base_graph), strong_components))
    return [[v for v in n.nodes()] for n in sinks]


def get_second_highest(l: List[Campaign]):
    # ToDo: random tie breaker
    l = Sorting.copy_and_sort_campaigns(l)
    if len(l) > 1:
        return l[1]
    elif len(l) == 1:
        # Here I insert a ghost campaign with zero budget. This is so that a winner does not ever pay its own bid.
        return Campaign("zzz", 1, 0.0, Good({'X'}, None, None))
    else:
        raise Exception("This should NEVER happen!")


def waterfall_old(m: Market) -> Tuple[Allocation, Dict[Campaign, Good]]:
    """
    Given a market, compute the waterfall outcome.
    :param m:
    :return:
    """
    # Book keeping structures
    alloca = {c: {g: 0 for g in m.goods} for c in m.campaigns}
    prices = {c: {g: 0.0 for g in m.goods} for c in m.campaigns}

    total_allocation = {c: 0 for c in m.campaigns}

    # Sort a shallow copy of campaigns to get the order of allocation
    list_of_ordered_campaigns = Sorting.copy_and_sort_campaigns(m.campaigns)

    remaining_supply = {g: g.supply for g in m.goods}

    while True:
        # Filter campaigns. Select only those campaigns that can be completely satisfied with remaining supply.
        list_of_ordered_campaigns = list(
            filter(lambda x, supply=remaining_supply: sum([remaining_supply[g] for g in m.goods if g.__matches__(x.target)]) >= x.reach, list_of_ordered_campaigns))
        # There are no remaining campaigns that can possibly be satisfied with the current supply, hence, the algorithm stops.
        if len(list_of_ordered_campaigns) == 0:
            break
        # Select the campaign with highest R/I
        c_high = list_of_ordered_campaigns[0]
        second_highest = {}
        # For each good, that is of interest to the winner campaign and that has remaining supply
        for g in m.goods:
            if g.__matches__(c_high.target) and remaining_supply[g] > 0:
                # Collect a list of campaigns that are also interested in this good. Note that the winner c_high must be here.
                c_list = [c for c in list_of_ordered_campaigns if g.__matches__(c.target)]
                # Record the second highest bid, i.e., the campaign whose R/I is the second highest
                second_highest[g] = get_second_highest(c_list)
        # Order all the bids for all the goods.
        list_of_bids = [(g, c) for g, c in second_highest.items()]
        list_of_bids.sort(key=lambda x: x[1], reverse=False)
        # Select the minimum, 2nd_highest bid as the next good to allocate, and price it at this 2nd_highest bid
        selected_g = list_of_bids[0][0]
        selected_price = list_of_bids[0][1].budget / list_of_bids[0][1].reach
        # Allocate as much as needed
        alloca[c_high][selected_g] = min(remaining_supply[selected_g], c_high.reach - total_allocation[c_high])
        # Book keeping
        remaining_supply[selected_g] -= alloca[c_high][selected_g]
        total_allocation[c_high] += alloca[c_high][selected_g]
        prices[c_high][selected_g] = selected_price
        # Check if the campaign was satisfied and remove it from the list.
        if total_allocation[c_high] >= c_high.reach:
            list_of_ordered_campaigns.remove(c_high)

    return Allocation(m, alloca), prices


expt_config['RESERVE_PRICES'] = {"Male-Young-High": initial_single_reserve,
                                 "Male-Young-Low": initial_single_reserve,
                                 "Male-Old-Low": initial_single_reserve,
                                 "Male-Old-High": initial_single_reserve,
                                 "Female-Young-High": initial_single_reserve,
                                 "Female-Young-Low": initial_single_reserve,
                                 "Female-Old-Low": initial_single_reserve,
                                 "Female-Old-High": initial_single_reserve}

# Read the reserve prices from the config file.
reserve_prices = {}
for s, r, in expt_config['RESERVE_PRICES'].items():
    l = [x.capitalize() for x in s.split("-")]
    l.sort()
    reserve_prices[Good(set("-".join(l).split("-")), None, None)] = float(r)
