import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter

filepath = '../results/expZ.zip'

eps = [0.03, 0.027, 0.024, 0.021, 0.018, 0.015]

trials = 0

# algos = ['random', 'gp', 'gpn']
algos = ['random', 'gpn']

# zfile = zipfile.ZipFile(filepath)

expt_id = 'experiment_calena_small'
b = 20

expt_id = 'experiment_calena_long'
b = 30


def get_data_for_eps(eps, zfile=None, b=20):
    algo_trial_data = {'random': {}, 'gp': {}, 'gpm': {}, 'gpn': {}}

    # for trial in [0, 1, 2, 3, 4, 5, 6, 7]:
    # for which_algo in ['gp', 'gpn', 'random']:
    for which_algo in ['gpm', 'gp', 'gpn', 'random']:
        # for trial in range(0, 20 if which_algo != 'gpn' else 13):  # Up to 20 looks ok
        for trial in range(0, 13):
            data = []
            for budget in range(0, b):
                # ifile = zfile.open("experiment_Z/" + which_algo + "/eps_" + str(eps) + "/trial_" + str(trial) + "/" + str(budget) + "/eq.txt")
                ifile = open(f'../../emd-adx-results/{expt_id}/{which_algo}/eps_{eps}/trial_{trial}/{budget}/eq.txt')
                with ifile as f:
                    first_line = f.readline()
                    data += [float(first_line)]

            running_max = [max(data[0:i + 1]) for i in range(0, b)]
            algo_trial_data[which_algo][trial] = running_max

    print(algo_trial_data)

    all_results = []
    for algo, data in algo_trial_data.items():
        print("\n ", algo)
        for trial, running_max in data.items():
            print(running_max)
            b = 0
            for m in running_max:
                all_results += [(algo, eps, trial, b, m)]
                b += 1
    dataframe = pd.DataFrame(all_results, columns=['algo', 'eps', 't', 'b', 'm'])
    # final_data = dataframe.groupby(by=['algo', 'eps', 'b', 't']).mean()
    final_data = dataframe.groupby(by=['algo', 'eps', 'b']).mean()
    final_data = final_data.reset_index()
    # final_data.to_csv('../results/bo/' + str(eps) + '.csv')
    return final_data


# data = get_data_for_eps(0.03, None)
# ax = plt.figure().gca()
# ax.xaxis.set_major_locator(MaxNLocator(integer=True))

# plt.plot([i for i in range(0, 20)], data[data['algo'] == 'random']['m'], label='random')
# plt.plot([i for i in range(0, 20)], data[data['algo'] == 'gp']['m'], label='gp')
# plt.legend()
# plt.show()

fig, axs = plt.subplots(ncols=2, nrows=1)
for i, eps in enumerate([0.03, 0.02]):
    sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(eps, None, b), ax=axs[i], hue_order=['random', 'gp', 'gpm', 'gpn'])
    axs[i].set_title(r"$\epsilon =$ " + str(eps))
    axs[i].set_ylabel("Running max. revenue" if i == 0 else "")
    axs[i].set_xlabel("# of reserve prices searched")
    axs[i].yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    axs[i].get_yaxis().set_visible(i == 0)
    # axs[i].set_ylim(0.15, 0.45)
    axs[i].legend(loc='lower right')

plt.show()
exit()

fig, axs = plt.subplots(ncols=3, nrows=2)
axs[0][0].set_title(r"$\epsilon = 0.03$")
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.03, zfile), ax=axs[0][0])
axs[0][1].set_title(r"$\epsilon = 0.027$")
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.027, zfile), ax=axs[0][1])
axs[0][2].set_title(r"$\epsilon = 0.024$")
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.024, zfile), ax=axs[0][2])
axs[1][0].set_title(r"$\epsilon = 0.021$")
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.021, zfile), ax=axs[1][0])
axs[1][1].set_title(r"$\epsilon = 0.018$")
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.018, zfile), ax=axs[1][1])
axs[1][2].set_title(r"$\epsilon = 0.015$")
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.015, zfile), ax=axs[1][2])

for i in range(0, 2):
    for j in range(0, 3):
        axs[i][j].set_xlabel("")

plt.show()
