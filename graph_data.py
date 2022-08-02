import copy
import glob
import json
import os
import re
from collections import defaultdict
from datetime import datetime

import scipy.special
import scipy.spatial.distance
import scipy.stats
import tabulate
from scipy.stats import ttest_ind_from_stats
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tqdm import tqdm

tqdm_args = {"ncols": 150, "bar_format": "{l_bar}{bar}|", "position": 0}
plt.rcParams.update({'font.size': 11})


# this class helps translate non human readable text to human readable text. If a human readable text is not available it defaults to the non human readable
# helps prevent errors in case I forget to add a translation
class StrTranslate(dict):
    def __getitem__(self, item):
        if item in self.keys():
            return super().__getitem__(item)
        else:
            return item


# matplotlib.use('WebAgg')
# todo: move these to be a property of the agent and DM classes so things are more organized?
agent_translation = StrTranslate({
    "SPA": "Simple Preference Agent",
    "SSA": "Simple Saliency Agent",
    "SA": "Saliency Agent",
    "MPA": "Move Pref. Agent",
    "MPSA": "Move Pref. Saliency Agent",
})
agent_names = list(agent_translation.keys())

dm_translation = StrTranslate({
    "BM": "Random Manager",
    "DMABM": "ε-Decay Manager",
    "EM": "Do-Nothing Manager",
    "IAM": "Iterative-All Manager",
    "MABM": "ε-Greedy Manager, ε=0.2",
    "MABM-e,0.05": "ε-Greedy Manager, ε=0.05",
    "MABM-e,0.1": "ε-Greedy Manager, ε=0.10",
    "MABM-e,0.3": "ε-Greedy Manager, ε=0.30",
    "OAM": "One-Of-Each Manager",
    "PMM": "Provide-Missing Manager",
    "TMABM": "Thompson Manager",
    "UCB1MABM": "UCB1 Manager",
    "UCB1TMABM": "UCB1-Tuned Manager",
    "OBM": "Oracle Best Manager",
})

# final_dm_names = [
#     "EM",
#     "BM",
#     "OAM",
#     "IAM",
#     "PMM",
#     "MABM",
#     "UCB1TMABM",
#     "TMABM",
#     "OBM",
# ]

score_name_translation = StrTranslate({
    "kl": "KL Div. Distance",
    "co": "Cosine Distance",
    "js": "Jensen-Shannon Distance",
    "nu": "Number of Distractions"
})


def ensure_dir(directory):
    # if it has a . in the path, we will just assume that this is a file and we need the dirname to proceed
    if os.path.splitext(os.path.basename(directory))[1] != "":
        base_dir = os.path.dirname(directory)
    else:
        base_dir = directory
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)


# region scoring
def cosine_arrays(a1, a2):
    return np.array([scipy.spatial.distance.cosine(i, j) for i, j in zip(a1, a2)])


def kl_div(a1, a2):
    return np.array([scipy.stats.entropy(i, j) for i, j in zip(a1, a2)])


def js_distance(a1, a2):
    return np.array([scipy.spatial.distance.jensenshannon(i, j) for i, j in zip(a1, a2)])


def len_array(arr):
    return np.array([len(v) for v in arr])


def score_data(data, dm, agent, scene_num):
    # change the interactions into a decimal value rather than a list
    interactions = [
        [{
            action_type: (interacts / attempts) if attempts != 0 else 1 for action_type, (interacts, attempts) in interaction.items()
        } for interaction in trial["interactions_record"]]
        for trial in data
    ]
    
    # normalize the interactions
    interactions = [[
        {
            action_type: (value / sum(interaction.values())) if sum(interaction.values()) > 0 else 1 / 5 for action_type, value in interaction.items()
        } for interaction in trial] for trial in interactions
    ]
    
    # bring the interactions back into the main data
    for i, _ in enumerate(data):
        data[i]["interactions_record"] = interactions[i]
    
    # change everything to np arrays
    # format: trial, measurement, turn, type
    # these keys need to be handled differently or not at all
    skip_keys = ["action_history", "distraction_record"]
    data_array = np.array([
        [[list(entry.values()) for entry in value_list] for key, value_list in trial.items() if key not in skip_keys]
        for trial in data
    ])
    extra_data_array = [
        {key: value_list for key, value_list in trial.items() if key in skip_keys}
        for trial in data
    ]
    
    data_scored = []
    for i, (trial, extra_trial) in enumerate(zip(data_array, extra_data_array)):
        # unpack each model
        static_model = trial[0]
        dynamic_model = trial[1]
        true_model = trial[2]
        interaction_model = trial[3]
        
        action_history = extra_trial["action_history"]
        if "distraction_record" in extra_trial:
            distraction_record = extra_trial["distraction_record"]
        else:
            print("distractions record does not exist, pretending it is empty")
            distraction_record = [[] for i in range(len(action_history))]
        
        # compare the models
        scores_by_type = {
            "kl_dynamic_v_true": kl_div(dynamic_model, true_model),
            "kl_dynamic_v_static": kl_div(dynamic_model, static_model),
            "kl_static_v_true": kl_div(static_model, true_model),
            "kl_interaction_v_true": kl_div(interaction_model, true_model),
            "js_dynamic_v_true": js_distance(dynamic_model, true_model),
            "js_dynamic_v_static": js_distance(dynamic_model, static_model),
            "js_static_v_true": js_distance(static_model, true_model),
            "js_interaction_v_true": js_distance(interaction_model, true_model),
            "cosine_dynamic_v_true": cosine_arrays(dynamic_model, true_model),
            "cosine_dynamic_v_static": cosine_arrays(dynamic_model, static_model),
            "cosine_static_v_true": cosine_arrays(static_model, true_model),
            "cosine_interaction_v_true": cosine_arrays(interaction_model, true_model),
            "num_distractions": len_array(distraction_record)
        }
        
        # add to dataframe array
        for score_type, scores in scores_by_type.items():
            for turn, score in enumerate(scores):
                data_scored.append({
                    "turn": turn,
                    "trial": i,
                    "score_type": score_type,
                    "score": score,
                    "DM": dm,
                    "Agent": agent,
                    "scene": scene_num,
                })
    
    return pd.DataFrame(data_scored)


# endregion


# region processing
def get_params(test_folder, force_old_method=False):
    params_file = f"{test_folder}/params.json"
    
    if os.path.exists(params_file) and not force_old_method:
        # if the file exists we will use it
        with open(params_file) as fp:
            params = json.load(fp)
    else:
        # otherwise we just decode the params from the folder name and contents
        dm_short, agent_short = os.path.basename(test_folder).split("+")
        params = {
            "agent_short": agent_short,
            "agent_name": agent_translation[agent_short],
            "dm_short": dm_short,
            "dm_name": dm_translation[dm_short],
            "scene_num": os.path.basename(os.path.dirname(test_folder)),
            "trials": len(glob.glob(f"{test_folder}/raw/*")),
            "initial_pref": None,
            "scene_pref": None,
        }
    
    return params


def cache_processing(date_folder, force_reprocessing=False):
    # gather all of the data
    # data currently has several places it can be
    #   1. output_data folder contains dated directories (since there is generally only a single run per day)
    #   2. within those folders we have "modes" or "scenarios" which dictate the preferences being tested
    #   3. within those folders is the specific directories  for tests of Agent vs Manager
    #   4. within those folders is the individual trials
    
    # Trials need to be averaged, so must all be processed together.
    # They also take a long time to process, so this processing is going to be cached (in case i want to see different graphs for the same data)
    
    # for scene_folder in glob.glob(f"{date_folder}/*"):
    date_name = os.path.basename(date_folder)
    for test_folder in tqdm(glob.glob(f"{date_folder}/*/*"), **tqdm_args, desc=date_name):
        cached_plot_file = f"{test_folder}/plots/plot.csv"
        # skip if we already have cached the processing
        if os.path.exists(cached_plot_file) and not force_reprocessing:
            continue
        
        # gather the pre-stats
        test_params = get_params(test_folder, force_old_method=True)
        dm = test_params["dm_name"]
        agent = test_params["agent_name"]
        scene_num = test_params["scene_num"]
        
        # load the data
        trial_data = []
        # check if there are npy files,
        
        npy_files = glob.glob(f"{test_folder}/raw/*.npy")
        json_files = glob.glob(f"{test_folder}/raw/*.json")
        trial_file = {os.path.splitext(os.path.basename(file))[0]: file for file in (npy_files + json_files)}
        for trial, file in trial_file.items():
            # we might still have json files, but currently it only looks for npy file
            file_extension = os.path.splitext(file)[1]
            if file_extension == ".json":
                with open(file, "r") as fp:
                    data: dict = json.load(fp)
            elif file_extension == ".npy":
                data: dict = np.load(file, allow_pickle=True).item()
            else:
                print(f"File is incorrect format, requires either .json or .npy. on file {file} with extension {file_extension}")
                assert False
            
            trial_data.append(data)
        
        # process the data
        long_df = score_data(trial_data, dm, agent, scene_num)
        
        # cache the results of processing the data
        ensure_dir(cached_plot_file)
        long_df.to_csv(cached_plot_file, index=False)


# endregion


# region graphing
def graph_data(dict_dfs, save=True, save_location="graphs", remove_scenario_label=False, no_graph_title=False, switch_agent_scene=False):
    if switch_agent_scene:
        primary_key = "scene"
        secondary_key = "Agent"
    else:
        primary_key = "Agent"
        secondary_key = "scene"
        
    # each agent is graphed separately
    for i, (key, key_df) in enumerate(dict_dfs.items()):
        # switch things around a bit for better readability
        no_x_label = False
        no_y_label = False
        no_legend = False
        no_scene_titles = False
        if not switch_agent_scene:
            # no_scene_titles = (agent != 'Exploration Focused Agent')
            # no_x_label = (agent != 'Novelty Focused Agent')
            no_legend = (key != 'Goal Focused Agent')
        
        # if there is more than one score type we default to the first, and filter the df to only include it
        score_type = key_df.score_type.unique()[0]
        key_df = key_df[key_df.score_type == score_type]
        score_name = score_name_translation[score_type[0:2]]
    
        # basic graph labels
        graph_title = f"{key}"
        x_label = "Turn Number"
        y_label = f"{score_name}"
        if switch_agent_scene:
            graph_title = graph_title.replace("2", " to ").replace("book_", "").replace("food_", "").replace("distract_", "").replace("_", " ").replace("  ", " ").title()
            pass
    
        # define the plots (and ensure that they are in an array since if we only ask for 1 we dont get an array back, which is dumb)
        num_plots = len(key_df[secondary_key].unique())
        fig, axes = plt.subplots(1, num_plots, sharey=True, sharex=True)
        if type(axes) != np.ndarray:
            axes = np.array([axes])
    
        # set size given number of plots
        # todo: these need to be generalized to any amount of plots
        fig.set_size_inches([5 * num_plots + 1, 4.8])
        
        # mess with the size todo: remove this hacky bs cuz it only for the paper
        fig_w, fig_h = fig.get_size_inches()
        fig.set_size_inches((fig_w, fig_h*.9))
    
        # actually draw each plot
        secondary_key_names = sorted(key_df[secondary_key].unique())
    
        # reorder them, todo: remove this line when it is not needed
        if secondary_key_names[0] == "Environment to Environment" and len(secondary_key_names) == 4:
            secondary_key_names = [secondary_key_names[i] for i in [0, 2, 1, 3]]
            
        # remove pesky IDE warnings
        # ax = None

        for i, secondary_key_name in enumerate(secondary_key_names):
            secondary_df = key_df[key_df[secondary_key] == secondary_key_name]
            ax = axes[i]
        
            is_middle = (i+1 == ((num_plots+1) // 2))
        
            plot = sns.lineplot(
                data=secondary_df,
                x="turn",
                y="score",
                hue="DM",
                # style="Agent",
                palette="colorblind",
                # ci="sd",
                ci=None,
                estimator=np.mean,
                ax=ax,
                legend=is_middle and not no_legend
            )

            # remove individual x and y labels
            plot.set_xlabel("")
            plot.set_ylabel("")
        
            # each plot gets its scene title
            if remove_scenario_label:
                scene_text = secondary_key_name.replace(" Actions", "") + " Action-Types"
                title_str = f"{scene_text}"
            else:
                title_str = f"Scenario {secondary_key_name + 1}" if type(secondary_key_name) == int else f"Scenario {secondary_key_name}"
            if switch_agent_scene:
                title_str = secondary_key_name
            if not no_scene_titles:
                plot.set_title(title_str)
        
        # if ax is not None:
        #     handles, labels = ax.get_legend_handles_labels()
        #     fig.legend(handles, labels, loc='upper center')
        
        # common ticks, todo: dont cheat with the y label
        x_label_pos = 0.515
        y_label_pos = 0.006
        if not no_y_label:
            fig.supylabel(y_label, x=y_label_pos)
        if not no_x_label:
            fig.supxlabel(x_label, x=x_label_pos)
        if not no_graph_title:
            fig.suptitle(graph_title, x=x_label_pos)
        
        plt.tight_layout(pad=0.5)
        
        if save:
            save_path = f"{save_location}/{key}.png"
            ensure_dir(save_path)
            plt.savefig(save_path)
        else:
            plt.show()
    

# endregion

def main():
    date_folder = f"output_data/2022-07-05"
    date = os.path.basename(date_folder)
    skip_agents = []
    skip_dms = []
    
    # first we process the data into a graph-able state, and cache that on disk
    cache_processing(date_folder, force_reprocessing=True)
    # cache_processing(date_folder)
    
    # load it all up again, and this time organize for graphing
    total_df = pd.concat([pd.read_csv(f"{test_folder}/plots/plot.csv") for test_folder in glob.glob(f"{date_folder}/*/*")], ignore_index=True)
    
    # this is just temporary, i changed the names around but did it in between runs so now i want them all to match.
    new_agent_translation = {
        'Move Pref. Agent': 'Exploration Focused Agent',
        'Saliency Agent': 'Novelty Focused Agent',
        'Simple Preference Agent': 'Goal Focused Agent',
        
        'Exploration Focused Agent': 'Exploration Focused Agent',
        'Novelty Focused Agent': 'Novelty Focused Agent',
        'Goal Focused Agent': 'Goal Focused Agent'
    }
    total_df.replace({"Agent": new_agent_translation}, inplace=True)
    
    # remove the steps before 90
    total_df = total_df[total_df["turn"] >= 90]
    
    # remove OAM from num distractions, it throws the scale of the graph completely off. and dont include turn 99? not sure what the second half of this statement is doing
    total_df = total_df[~(
            ((total_df.score_type == "num_distractions") & (total_df.DM == "One-Of-Each Manager"))
            | ((total_df.score_type == "num_distractions") & (total_df.turn == 99))
    )]
    
    # graph everything
    # graph_scores(total_df, date, skip_agents)
    pass


def graph_scores(total_df, date, skip_agents=(), score_type_override=None):
    if score_type_override is None:
        score_types = total_df.score_type.unique()
    else:
        score_types = score_type_override
    for score_type in tqdm(score_types, **tqdm_args, desc="Scoring"):
        # split by method
        score_type_df = total_df[total_df.score_type == score_type]
        
        # further split by agent, as that is how we graph
        agent_dfs = {agent: score_type_df[score_type_df.Agent == agent] for agent in score_type_df.Agent.unique() if agent not in skip_agents}
        
        # graph
        graph_data(
            agent_dfs,
            save_location=f"output_graphs/{date}/{score_type}",
            remove_scenario_label=True,
            no_graph_title=True,
        )
        
        # close resulting figures to free memory
        plt.close("all")
        pass
    
    
# this is for the appendix because the normal way of graphing makes the graphs too wide to read.
def graph_appendix(total_df, date):
    # only consider the js_dynamic_v_true score type, cuz its the only one we actually care about
    score_type = "js_dynamic_v_true"
    total_df = total_df[total_df.score_type == score_type]
    
    # further split by scene, as that is how we graph
    scene_dfs = {scene: total_df[total_df.scene == scene] for scene in total_df.scene.unique()}
    
    # graph
    graph_data(
        scene_dfs,
        save_location=f"output_graphs/{date}/{score_type}",
        remove_scenario_label=False,
        switch_agent_scene=True
    )
    
    # close resulting figures to free memory
    plt.close("all")
    pass


def final_data_table(total_df):
    p_value_test = 0.0001
    
    # extract things at the right turn
    final_turn = total_df.turn.max()
    score_df = total_df[(total_df.score_type == "kl_dynamic_v_true") & (total_df.turn == final_turn)]
    # calculate mean, std, and n_obs
    stats_df = score_df.groupby(["DM", "Agent", "scene"], as_index=False).mean()
    stats_df["std_"] = score_df.groupby(["DM", "Agent", "scene"], as_index=False).std()["score"]
    stats_df["n_obs"] = score_df.groupby(["DM", "Agent", "scene"], as_index=False).count()["score"]
    
    # get rid of useless cols, and rename "score" to "mean"
    stats_df["avg"] = stats_df["score"]
    stats_df = stats_df[['DM', 'Agent', 'scene', 'avg', 'std_', 'n_obs']]

    # isolate random manager to test against
    mean_std_test = stats_df[stats_df.DM == "Random Manager"]
    
    # remove random manager from the stats df
    # stats_df = stats_df[stats_df.DM != "Random Manager"]
    
    def do_t_test(row):
        mean_base, std_base, n_obs_base = mean_std_test[(mean_std_test.Agent == row.Agent) & (mean_std_test.scene == row.scene)][['avg', 'std_', 'n_obs']].iloc[0]
        mean, std, n_obs = row[['avg', 'std_', 'n_obs']]
        stat, pvalue = ttest_ind_from_stats(mean, std, n_obs, mean_base, std_base, n_obs_base)
        return (pvalue < p_value_test) and (stat < 0)
        
    # apply student t-test
    stats_df["significant"] = stats_df.apply(do_t_test, axis=1)
    # used to figure the best
    stats_df["best"] = False
    
    # organize the data so tabulate can handle it the way i want
    preferred_col_order = ['Agent', 'Random Manager', 'Provide-Missing Manager', 'ε-Greedy Manager', 'UCB1-Tuned Manager', 'Thompson Manager', 'One-Of-Each Manager']
    organized_data = defaultdict(dict)
    for scene in stats_df.scene.unique():
        scene_df = stats_df[stats_df.scene == scene]
        
        scene_text = scene.replace(" Actions", "") + " Action-Types"
        
        scenario_row = r"\hline" + "\n" + r"\multicolumn{" + str(len(score_df.DM.unique()) + 1) + r"}{c}" + f"{{{scene_text}}}"
        organized_data[scene] = {"Agent": scenario_row}
        
        # for each agent, figure out which one is the best. todo: this is a bad way to do it, figure out how to move this on stats_df
        for agent in scene_df.Agent.unique():
            scene_df.loc[scene_df[(scene_df.Agent == agent) & (scene_df.DM != "One-Of-Each Manager")].avg.idxmin(), "best"] = True
        
        for i, row in scene_df.iterrows():
            is_important_pre = r"\textit{" if row.significant else ""
            is_important_post = "}" if row.significant else ""
            
            is_best_pre = r"\textbf{" if row.best else ""
            is_best_post = "}" if row.best else ""
            
            table_entry_str = f"{is_best_pre}{is_important_pre}{row.avg:.3f}±{row.std_:.3f}{is_important_post}{is_best_post}"
            table_entry_str = table_entry_str.replace("±", r"$\pm$")
            organized_data[f"{row.Agent} {row.scene}"]["Agent"] = row.Agent.replace("Agent", "").replace("Preference", "Pref.")
            organized_data[f"{row.Agent} {row.scene}"][row.DM] = table_entry_str

    # now make it in the correct order todo: this makes no sense as a general thing, and is only for the paper, remove and do properly later.
    organized_data = {row_name: {k: data[k] for k in preferred_col_order} if len(data) > 1 else data for row_name, data in organized_data.items()}
    organized_data = {list(organized_data.keys())[i]: organized_data[list(organized_data.keys())[i]] for i in [0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 12, 13, 14, 15]}
    
    # print the tabulated
    headers = {
        title: title
        for title in list(organized_data.values())[0].keys()
    }
    values = list(organized_data.values())
    tabulated = tabulate.tabulate(values, tablefmt="latex_raw", headers=headers)

    # replace some things
    # proper epsilon
    tabulated = tabulated.replace(r"ε", r"$\epsilon$")
    # remove extra "Manager"
    tabulated = tabulated.replace("Manager", "")
    # fix the multiline stuff i did earlier
    tabulated = re.sub("( +&){6} +\\\\", "\\\\", tabulated)
    # remove extra horizontal lines and the begin{tabular} + alignment thing (i already have that down)
    tabulated = "\n".join([line for i, line in enumerate(tabulated.split("\n")) if i not in [0, 1, 3]])
    
    # print(tabulated)
    with open("table.txt", "w") as fp:
        fp.write(tabulated)
    pass
    
    
def final_graphs_and_chart():
    # date_folder = f"output_data/merge_to_UCB"
    # date_folder = f"output_data/merge_to_epsilons"
    date_folder = "output_data/2022-05-30"
    date = os.path.basename(date_folder) + "_new"
    
    total_df = pd.concat([pd.read_csv(f"{test_folder}/plots/plot.csv") for test_folder in glob.glob(f"{date_folder}/*/*")], ignore_index=True)
    
    # I renamed MPA2 to "Exploring Focused Agent" from the original, and want to make it go back to saying the original "Exploration Focused Agent"
    new_agent_translation = {
        'Move Pref. Agent': 'Exploration Focused Agent',
        'Saliency Agent': 'Novelty Focused Agent',
        'Simple Preference Agent': 'Goal Focused Agent',
        
        'Exploration Focused Agent': 'Exploration Focused Agent',
        'Exploring Focused Agent': 'Exploration Focused Agent',
        'Novelty Focused Agent': 'Novelty Focused Agent',
        'Goal Focused Agent': 'Goal Focused Agent'
    }
    total_df.replace({"Agent": new_agent_translation}, inplace=True)
    
    scene_names = list(total_df.scene.unique())
    scene_split = {name: name.split("2") for name in scene_names}
    
    action_classes = {
        "Environment": ["talk", "touch", "look"],
        "Missing": ["distract_food_eat", "distract_book_read"],
    }
    
    reverse_action_classes = {}
    for action_class, action_types in action_classes.items():
        reverse_action_classes = {**reverse_action_classes, **{action_type: action_class for action_type in action_types}}
        
    scene_organize = {name: f"{reverse_action_classes[action1]} to {reverse_action_classes[action2]}" for name, (action1, action2) in scene_split.items()}
    
    # overwrite the old scene labels with these broader categories
    total_df["scene"] = total_df.scene.apply(lambda x: scene_organize[x])

    # remove the steps before 90
    total_df = total_df[total_df["turn"] >= 90]
    
    # create the data table
    # final_data_table(total_df)

    # remove OAM from num distractions, it throws the scale of the graph completely off. and dont include turn 99? not sure what the second half of this statement is doing
    total_df = total_df[~(((total_df.score_type == "num_distractions") & (total_df.DM == "One-Of-Each Manager")) | ((total_df.score_type == "num_distractions") & (total_df.turn == 99)))]
    
    total_df.to_csv("cached_final/total_df.csv")
    print(date)

    # graph_scores(total_df, date, score_type_override=["js_dynamic_v_true"])
    # final_data_table(total_df)
    pass


def cached_graph_final():
    total_df = pd.read_csv("cached_final/total_df.csv")
    date = "2022-05-30_new"
    graph_scores(total_df, date, score_type_override=["js_dynamic_v_true"])
    pass


def appendix_graphs():
    date_folder = "output_data/2022-05-30"
    date = os.path.basename(date_folder) + "_appendix"
    appendix_df = pd.concat([pd.read_csv(f"{test_folder}/plots/plot.csv") for test_folder in glob.glob(f"{date_folder}/*/*")], ignore_index=True)
    
    new_agent_translation = {
        'Move Pref. Agent': 'Exploration Focused Agent',
        'Saliency Agent': 'Novelty Focused Agent',
        'Simple Preference Agent': 'Goal Focused Agent',
        
        'Exploration Focused Agent': 'Exploration Focused Agent',
        'Exploring Focused Agent': 'Exploration Focused Agent',
        'Novelty Focused Agent': 'Novelty Focused Agent',
        'Goal Focused Agent': 'Goal Focused Agent'
    }
    appendix_df.replace({"Agent": new_agent_translation}, inplace=True)
    
    # remove the steps before 90
    appendix_df = appendix_df[appendix_df["turn"] >= 90]
    
    appendix_df = appendix_df[~(((appendix_df.score_type == "num_distractions") & (appendix_df.DM == "One-Of-Each Manager")) | ((appendix_df.score_type == "num_distractions") & (appendix_df.turn == 99)))]
    
    # write to file because the appending process at the beginning takes forever
    appendix_df.to_csv("cached_final/appendix_df.csv")
    print(date)

    # graph_scores(appendix_df, date, score_type_override=["js_dynamic_v_true"])
    
    pass


def cached_graph_appendix():
    appendix_df = pd.read_csv("cached_final/appendix_df.csv")
    date = "2022-05-30_appendix"
    graph_appendix(appendix_df, date)
    pass


if __name__ == '__main__':
    # main()
    # final_graphs_and_chart()
    # cached_graph_final()
    # appendix_graphs()
    cached_graph_appendix()
    # graph_scores(pd.read_pickle("total_df.npy"), "test", score_type_override=["js_dynamic_v_true"])
    # final_data_table(pd.read_pickle("total_df.npy"))
