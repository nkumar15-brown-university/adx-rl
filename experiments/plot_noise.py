import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

num_initial_points = 5
only_means = False
restricted = False
# First, combine all the results into a single dataframe.
dfs = []
for i in range(0, 5):
    temp_df = pd.read_csv('../results/small_bo/small_bo_part' + str(i + 1) + '/small_bo_' + str(num_initial_points) + '.csv')
    # Update the trial number
    temp_df.trial = temp_df.trial + i * 10
    dfs += [temp_df]
data = pd.concat(dfs)

# Convert minima to maxima
data['value'] = -1.0 * data['value']

# Compute cumulative maxima
frames = []
algo_set = ['gp', 'gpm', 'random'] if restricted else ['gp', 'gpnoisy', 'gpm', 'gpmnoisy', 'gpn', 'random']
for algo in algo_set:
    for eps in [0.03, 0.02, 0.01]:
        for delta in [0.3, 0.2, 0.1]:
            for trial in range(0, 10):
                x = data[(data['algo'] == algo) & (data['eps'] == eps) & (data['delta'] == delta) & (data['trial'] == trial)]
                x['cummax'] = x['value'].cummax()
                frames += [x]
df = pd.concat(frames)

# Plot.
fig, axs = plt.subplots(ncols=3, nrows=3, figsize=(20, 10))
for i, delta in enumerate([0.3, 0.2, 0.1]):
    for j, eps in enumerate([0.03, 0.02, 0.01]):
        print(i, j, delta, eps)
        if not only_means:
            the_df = df[(df['eps'] == eps) & (df['delta'] == delta)]
        else:
            the_df = df[(df['eps'] == eps) & (df['delta'] == delta)].groupby(['algo', 'b']).mean()
            the_df = the_df.reset_index()
        ax = sns.lineplot(x='b', y='cummax', hue='algo', style='algo', data=the_df, ax=axs[i][j])
        axs[i][j].set_title(f"epsilon = {eps},  delta = {delta}")
        axs[i][j].set_xlabel("")
        axs[i][j].set_ylim(-0.2, 0.26)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
fig.suptitle(f'num_initial_points = {num_initial_points}')
# plt.show()
plt.savefig(f'../results/small_bo/{"restricted" if restricted else "full"}/{"only_means" if only_means else "ci"}/num_init_x_{num_initial_points}.png')
