import matplotlib.pyplot as plt
import zipfile
import seaborn as sns
import pandas as pd

filepath = '../results/expZ.zip'

eps = [0.03, 0.027, 0.024, 0.021, 0.018, 0.015]

trials = 9

algos = ['random', 'gp', 'gpn']

zfile = zipfile.ZipFile(filepath)
which_algo = 'gp'


# eps = 0.015


def get_data_for_eps(eps, zfile):
    algo_trial_data = {'random': {}, 'gp': {}, 'gpn': {}}

    for trial in [0, 1, 2, 3, 4, 5, 6, 7]:
        for which_algo in ['gp', 'gpn', 'random']:
            data = []
            for budget in range(0, 20):
                ifile = zfile.open("experiment_Z/" + which_algo + "/eps_" + str(eps) + "/trial_" + str(trial) + "/" + str(budget) + "/eq.txt")
                with ifile as f:
                    first_line = f.readline()
                    data += [float(first_line)]

            running_max = [max(data[0:i + 1]) for i in range(0, 20)]
            algo_trial_data[which_algo][trial] = running_max

    print(algo_trial_data)

    all_results = []
    for algo, data in algo_trial_data.items():
        print("\n ", algo)
        for trial, running_max in data.items():
            print(running_max)
            b = 0
            for m in running_max:
                all_results += [(algo, eps, trial, b, m / 150.0)]
                b += 1
    dataframe = pd.DataFrame(all_results, columns=['algo', 'eps', 't', 'b', 'm'])
    # final_data = dataframe.groupby(by=['algo', 'eps', 'b']).mean()
    final_data = dataframe.groupby(by=['algo', 'eps', 'b', 't']).mean()
    final_data = final_data.reset_index()
    final_data.to_csv('../results/bo/'+str(eps) + '')
    return final_data


fig, axs = plt.subplots(ncols=3, nrows=2)
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.03, zfile), ax=axs[0][0])
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.027, zfile), ax=axs[0][1])
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.024, zfile), ax=axs[0][2])
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.021, zfile), ax=axs[1][0])
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.018, zfile), ax=axs[1][1])
sns.lineplot(x="b", y="m", hue="algo", style="algo", data=get_data_for_eps(0.015, zfile), ax=axs[1][2])
plt.show()
