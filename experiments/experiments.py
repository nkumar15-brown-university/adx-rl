from we_wf_experiments import run_we_wf_experiments
from singletonsetup import SingletonSetup
from bo_util import safe_create_dir
from game.statistics import compute_statistics
from prettytable import PrettyTable
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import numpy as np


def run_a_game_on_range(num_we, num_wf, k, start, end, m, reach_discount_factor, setup_base_goods, setup_pmf_base, setup_possible, setup_pmf_target, verbose):
    results = []
    for t in range(start, end):
        results.append(run_a_game(num_we, num_wf, k, t, m, reach_discount_factor, setup_base_goods, setup_pmf_base, setup_possible, setup_pmf_target, verbose))
    return results


def run_a_game(num_we, num_wf, k, t, m, reach_discount_factor, setup_base_goods, setup_pmf_base, setup_possible, setup_pmf_target, verbose):
    if verbose:
        print("\r" + "(WE, WF) = (", num_we, ",", num_wf, ") \t -> \t " + str((t / (m - 1)) * 100) + "% done", end="")
    # All fixed parameters are ready, can run an experiment now.
    we_c, wf_c, the_allocations, the_expenditure = run_we_wf_experiments(reach_discount_factor,
                                                                         k,
                                                                         num_we,
                                                                         num_wf,
                                                                         setup_base_goods,
                                                                         setup_pmf_base,
                                                                         setup_possible,
                                                                         setup_pmf_target,
                                                                         verbose)
    utilities, total_expenditure = compute_statistics(the_allocations, the_expenditure)
    if verbose:
        print("*** Final Report ***")
        final_report_table = PrettyTable()
        final_report_table.field_names = ['Campaign', 'Good', 'Allocation', 'Expenses']
        final_report_table.align['Campaign'] = "l"
        final_report_table.align['Good'] = "l"
        final_report_table.align['Allocation'] = "c"
        for c, m in the_allocations.items():
            for g, a in m.items():
                if a > 0:
                    final_report_table.add_row([c, g, a, the_expenditure[c][g]])
        print(final_report_table)

        print("\n*** Final Utilities ***")
        final_utilities_table = PrettyTable()
        final_utilities_table.field_names = ['Campaign', 'Utility']
        final_utilities_table.align['Campaign'] = "l"
        final_utilities_table.align['Utility'] = "l"
        for c, u in utilities.items():
            final_utilities_table.add_row([c, u])
        print(final_utilities_table)
        print("Total auctioneer revenue = ", total_expenditure)

    # Record the utility of a we (wf) as the utility of the first player playing we (wf)
    we_utility = utilities[we_c[0]] if len(we_c) > 0 else 0.0
    wf_utility = utilities[wf_c[0]] if len(wf_c) > 0 else 0.0
    return num_we, num_wf, we_utility, wf_utility, total_expenditure


def estimate_a_single_game(setup_obj: SingletonSetup, file: str = None, verbose: bool = False, serial: bool = True):
    """
    Estimate a single game. Saves results in the corresponding experiment folder.
    :param setup_obj:
    :param verbose:
    :param file:
    :param serial:
    :return:
    """
    k = setup_obj.k
    n = setup_obj.n
    reach_discount_factor = setup_obj.reach_discount_factor
    m = setup_obj.number_of_samples_per_profile()

    results = []
    if verbose:
        print("\n++++++++ Start Experiment: ++++++++\n Collecting ", m, " samples for each profile for eps = ", setup_obj.eps, ", and budget = ", setup_obj.budget)
    if serial:
        for num_we in range(0, n + 1):
            num_wf = n - num_we
            if verbose:
                print("")
            for t in range(0, m):
                results.append(run_a_game(num_we=num_we,
                                          num_wf=num_wf,
                                          k=k,
                                          t=t,
                                          m=m,
                                          reach_discount_factor=reach_discount_factor,
                                          setup_base_goods=setup_obj.base_goods,
                                          setup_pmf_base=setup_obj.pmf_base_goods,
                                          setup_possible=setup_obj.possible_campaign_targets,
                                          setup_pmf_target=setup_obj.pmf_target_goods,
                                          verbose=verbose))
    else:
        with ProcessPoolExecutor(cpu_count()) as executor:
            chunk_size = 1000
            ends = np.arange(start=0, stop=m, step=chunk_size).astype(int)
            ends = ends[1:].tolist() + [m]
            starts = [0] + ends[:-1]

            futures = []
            for num_we in range(0, n + 1):
                num_wf = n - num_we
                for start, end in zip(starts, ends):
                    if verbose:
                        print(f"running from {start} to {end}")
                    futures.append(executor.submit(run_a_game_on_range,
                                                   num_we=num_we,
                                                   num_wf=num_wf,
                                                   k=k,
                                                   start=start,
                                                   end=end,
                                                   m=m,
                                                   reach_discount_factor=reach_discount_factor,
                                                   setup_base_goods=setup_obj.base_goods,
                                                   setup_pmf_base=setup_obj.pmf_base_goods,
                                                   setup_possible=setup_obj.possible_campaign_targets,
                                                   setup_pmf_target=setup_obj.pmf_target_goods,
                                                   verbose=verbose))
                if verbose:
                    print(f'submitted {len(starts)} jobs', flush=True)
            for future in as_completed(futures):
                exp = future.exception()
                # If an exception occurred, save it to a file and keep going.
                if exp is not None:
                    error_log_dir = f'../results/experiments/experiment_{setup_obj.expt_id}/error/'
                    safe_create_dir(error_log_dir, False)
                    with open(f'{error_log_dir}error.txt', "a") as f:
                        f.write(f'An exception of type {type(exp)} occurred: {exp} \n')
                    print(f'An exception occurred: {exp}')

                else:
                    result = future.result()
                    results.extend(result)

    df_results = pd.DataFrame(results, columns=['num_WE', 'num_WF', 'we', 'wf', 'revenue'])
    df_results = df_results.sort_values(['num_WE', 'num_WF'], ascending=[True, False])
    if verbose:
        print(f'\nwriting to file {file}')
    df_results.to_csv(file, index=False)
    # print("\n\n Average time per simulation = ", total_time / ((n + 1) * m))
    # print("++++++++ End ++++++++ \n")
