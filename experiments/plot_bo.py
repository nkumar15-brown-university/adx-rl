from skopt.acquisition import gaussian_ei
import matplotlib.pyplot as plt
import numpy as np


def plot_bo(f, n, res, noise_level):
    plt.rcParams["figure.figsize"] = (8, 14)

    x = np.linspace(0.5, 1.5, 400).reshape(-1, 1)
    x_gp = res.space.transform(x.tolist())
    fx = np.array([f(x_i) for x_i in x])

    # Plot the first n iterations
    print("n = ", n)
    for n_iter in range(n):
        print("n_iter = ", n_iter)
        gp = res.models[n_iter]
        curr_x_iters = res.x_iters[:n_iter + 1]
        curr_func_vals = res.func_vals[:n_iter + 1]
        print("res.func_vals = ", res.func_vals)
        print("curr_func_vals = ", curr_func_vals)

        # Plot true function.
        plt.subplot(n, 2, 2 * n_iter + 1)
        plt.plot(x, fx, "r--", label="True (unknown)")
        plt.fill(np.concatenate([x, x[::-1]]),
                 np.concatenate([fx - 1.9600 * noise_level,
                                 fx[::-1] + 1.9600 * noise_level]),
                 alpha=.2, fc="r", ec="None")

        # Plot GP(x) + contours
        y_pred, sigma = gp.predict(x_gp, return_std=True)
        plt.plot(x, y_pred, "g--", label=r"$\mu_{GP}(x)$")
        plt.fill(np.concatenate([x, x[::-1]]),
                 np.concatenate([y_pred - 1.9600 * sigma,
                                 (y_pred + 1.9600 * sigma)[::-1]]),
                 alpha=.2, fc="g", ec="None")

        # Plot sampled points
        plt.plot(curr_x_iters, curr_func_vals,
                 "r.", markersize=8, label="Observations")

        # Adjust plot layout
        plt.grid()

        if n_iter == 0:
            plt.legend(loc="best", prop={'size': 6}, numpoints=1)

        if n_iter != n:
            plt.tick_params(axis='x', which='both', bottom='off',
                            top='off', labelbottom='off')

            # Plot EI(x)
        plt.subplot(n, 2, 2 * n_iter + 2)
        # print("x_gp = ", x_gp)
        # print("curr_func_vals = ", curr_func_vals)
        # print("min = ", np.min(curr_func_vals))
        acq = gaussian_ei(x_gp, gp, y_opt=np.min(curr_func_vals))
        plt.plot(x, acq, "b", label="EI(x)")
        plt.fill_between(x.ravel(), -2.0, acq.ravel(), alpha=0.3, color='blue')

        next_x = res.x_iters[n_iter]
        next_acq = gaussian_ei(res.space.transform([next_x]), gp, y_opt=np.min(curr_func_vals))
        plt.plot(next_x, next_acq, "bo", markersize=6, label="Next query point")

        # Adjust plot layout
        plt.ylim(0, 0.1)
        plt.grid()

        if n_iter == 0:
            plt.legend(loc="best", prop={'size': 6}, numpoints=1)

        if n_iter != n:
            plt.tick_params(axis='x', which='both', bottom='off',
                            top='off', labelbottom='off')

    plt.show()
