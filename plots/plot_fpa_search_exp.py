import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from experiments.fpa import expected_revenue_uniform_case

base_dir = '../../emd-adx-results/fpa'
algo = 'random'
eps = 0.01
trial = 0


def get_one_df(base_dir, algo, eps, trial):
    temp_df = pd.DataFrame()
    data = pd.read_csv(f'{base_dir}/{algo}/eps_{eps}/trial_{trial}/result.csv')
    data['revenue'] = data['revenue'] * -1
    data['run_max'] = data['revenue'].cummax()

    temp_df['step'] = data['step']
    temp_df['reserve'] = data['reserve']
    temp_df['run_max'] = data['run_max']
    temp_df['anal_revenue'] = data['reserve'].apply(lambda x: expected_revenue_uniform_case(x, 2))
    temp_df['anal_run_max'] = temp_df['anal_revenue'].cummax()
    temp_df['trial'] = trial
    temp_df['eps'] = eps
    temp_df['algo'] = algo
    return temp_df


all_dfs = []
for algo in ['random', 'gp', 'gpn', 'gpm']:
    for eps in [0.02, 0.01]:
        for trial in range(0, 30):
            # print(f'algo = {algo}, eps = {eps}, trial = {trial}')
            all_dfs.append(get_one_df(base_dir, algo, eps, trial))
final_df = pd.concat(all_dfs)
print(final_df)
# final_df = final_df[final_df['step'] >= 0]
final_df = final_df.groupby(by=['algo', 'eps', 'step']).mean()
final_df = final_df.reset_index()

analytical_revenue = expected_revenue_uniform_case(0.5, 2)
fig, axs = plt.subplots(ncols=2, nrows=1)
for i, eps in enumerate([0.02, 0.01]):
    sns.lineplot(x="step", y="run_max", hue="algo", style="algo", data=final_df[final_df['eps'] == eps], ax=axs[i], hue_order=['random', 'gp', 'gpm', 'gpn'])
    #sns.lineplot(x="step", y="anal_run_max", hue="algo", style="algo", data=final_df[final_df['eps'] == eps], ax=axs[i], hue_order=['random', 'gp', 'gpm', 'gpn'])
    axs[i].set_title(r"$\epsilon =$ " + str(eps))
    axs[i].set_ylabel("Running max. revenue" if i == 0 else "")
    axs[i].set_xlabel("# of reserve prices searched")
    axs[i].legend(loc='lower right')
    axs[i].get_yaxis().set_visible(i == 0)
    #axs[i].axhline(y=analytical_revenue, linestyle=':', linewidth=0.5, color='black')
    # axs[i].axhline(y=analytical_revenue - eps)
    # axs[i].axhline(y=analytical_revenue + eps)
    # axs[i].set_yscale('log')
plt.show()
