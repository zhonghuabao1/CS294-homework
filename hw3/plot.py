import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import json
import os

"""
Using the plotter:

Call it from the command line, and supply it with logdirs to experiments.
Suppose you ran an experiment with name 'test', and you ran 'test' for 10
random seeds. The runner code stored it in the directory structure

    data
    L test_EnvName_DateTime
      L  0
        L log.txt
        L params.json
      L  1
        L log.txt
        L params.json
       .
       .
       .
      L  9
        L log.txt
        L params.json

To plot learning curves from the experiment, averaged over all random
seeds, call

    python plot.py data/test_EnvName_DateTime --value AverageReturn

and voila. To see a different statistics, change what you put in for
the keyword --value. You can also enter /multiple/ values, and it will
make all of them in order.


Suppose you ran two experiments: 'test1' and 'test2'. In 'test2' you tried
a different set of hyperparameters from 'test1', and now you would like
to compare them -- see their learning curves side-by-side. Just call

    python plot.py data/test1 data/test2

and it will plot them both! They will be given titles in the legend according
to their exp_name parameters. If you want to use custom legend titles, use
the --legend flag and then provide a title for each logdir.

"""

def plot_data(data, value="AverageReturn"):
    if isinstance(data, list):
        data = pd.concat(data, ignore_index=True)

    t = 'Iteration' if 'Iteration' in data.columns else 'Timestep'
    xlabel = t
    v = max(data[t])
    if v > 2e6:
        data[t] = ['%.2f'%(float(i) / 1e6) for i in data[t]]
        xlabel += '(1e6)'
    elif v > 2e5:
        data[t] = ['%.2f'%(float(i) / 1e5) for i in data[t]]
        xlabel += '(1e5)'

    sns.set(style="darkgrid", font_scale=1.1)
    sns.tsplot(data=data, time=t, value=value, unit="Unit", condition="Condition")
    plt.legend(loc='best').draggable()
    plt.xlabel(xlabel)


def build_data(fpath, condition=None):
    unit = 0
    data = []
    for root, dir, files in os.walk(fpath):
        if 'log.txt' in files:
            param_path = open(os.path.join(root,'params.json'))
            params = json.load(param_path)
            exp_name = params.get('exp_name') or '1'

            log_path = os.path.join(root,'log.txt')
            experiment_data = pd.read_table(log_path)

            experiment_data.insert(
                len(experiment_data.columns),
                'Unit',
                unit
                )
            experiment_data.insert(
                len(experiment_data.columns),
                'Condition',
                condition or exp_name
                )

            data.append(experiment_data)
            unit += 1

    return data


def main():
    print('''
usage:

python3 plot.py folder1 folder2 folder3 --legend name1 name2 name3

example:

python3 plot.py \
    data/ac_1_1_CartPole-v0_23-07-2019_15-46-07 \
    data/ac_100_1_CartPole-v0_23-07-2019_15-47-28 \
    data/ac_1_100_CartPole-v0_23-07-2019_15-48-33 \
    --legend ntu1_ngsptu1 ntu100_ngsptu1 ntu1_ngsptu100 \
    -s 'data/CartPole-v0(ntu-ngsptu).png'
''')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('logdir', nargs='*')
    parser.add_argument('--legend', nargs='*')
    parser.add_argument('--value', default='AverageReturn', nargs='*')
    parser.add_argument('--save', '-s', default='')
    args = parser.parse_args()

    use_legend = False
    if args.legend is not None:
        assert len(args.legend) == len(args.logdir), \
            "Must give a legend title for each set of experiments."
        use_legend = True

    data = []
    if use_legend:
        for logdir, legend_title in zip(args.logdir, args.legend):
            data += build_data(logdir, legend_title)
    else:
        for logdir in args.logdir:
            data += build_data(logdir)

    if isinstance(args.value, list):
        values = args.value
    else:
        values = [args.value]
    for value in values:
        plot_data(data, value=value)

    if args.save:
        plt.savefig(args.save)
    plt.show()

if __name__ == "__main__":
    main()
