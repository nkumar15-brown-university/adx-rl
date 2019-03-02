import zipfile

expt_id = 'M'
filepath = '../results/exp' + expt_id + '.zip'
zfile = zipfile.ZipFile(filepath)
which_algo = 'random'
eps = 0.03
trial = 0
budget = 0
ifile = zfile.open('experiment_' + expt_id + '/' + which_algo + "/eps_" + str(eps) + "/trial_" + str(trial) + "/" + str(budget) + "/eq.txt")
for l in ifile:
    print(l)

ifile = zfile.open('experiment_' + expt_id + '/' + which_algo + "/eps_" + str(eps) + "/trial_" + str(trial) + "/" + str(budget) + "/config.ini")
for l in ifile:
    print(l)
