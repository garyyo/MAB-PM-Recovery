from generate_preference_distributions import all_modes_iterator
from main import *


# these are weird huh
def backgen_90_history(pre_pref, pre_name):
    time_it()
    # set up the game, using the regular manager because it does nothing
    dm, agent, env, requested_infos = set_up_game(dm_type=BaseManager)
    obs, infos, old_infos, done, score = initialize_game(env, requested_infos)
    dm.save_output = True
    
    mode_name = f"{pre_name}"
    
    agent.preferred_actions = pre_pref
    before_pref_path = generate_preference_distributions.save_mode(mode_name, pre_pref)
    game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=False, max_turn_count=90)
    _, _, before_history_path = dm.output_data("backhistory", "pref-before", scene_num=mode_name)

    return before_history_path, before_pref_path, mode_name
    
    
def backgen_10_history(before_history_path, before_pref_path, pre_name, post_pref, post_name):
    time_it()
    # set up the game, using the regular manager because it does nothing
    dm, agent, env, requested_infos = set_up_game(dm_type=BaseManager)
    obs, infos, old_infos, done, score = initialize_game(env, requested_infos)
    dm.save_output = True
    
    mode_name = f"{pre_name}2{post_name}"

    # load the correct back history
    action_history = dm.load_backhistory(before_history_path)
    # set our agent's preferences to match
    agent.preferred_actions = post_pref

    # copy over the action history to the agent.
    agent.action_history = copy.deepcopy(action_history)
    
    # generate 10 turns of gameplay with post pref model
    after_pref_path = generate_preference_distributions.save_mode(mode_name, post_pref)
    game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=False, max_turn_count=10)
    _, _, after_history_path = dm.output_data("backhistory", "pref-after", scene_num=mode_name)
    
    return after_history_path, after_pref_path, mode_name


def load_all_history(pre_name, post_name):
    mode_name = f"{pre_name}2{post_name}"

    after_pref_path = f"backhistory/{mode_name}/preference_dist.json"
    after_history_path = f"backhistory/{mode_name}/BM/raw/pref-after.npy"
    
    return after_history_path, after_pref_path, mode_name


def main_all_scenarios():
    trials = 50
    max_turn_count = g_max_turn_count
    agent_types = [
        (SimplePreferenceAgent, {}),
        (SaliencyAgent, {}),
        (MovePrefAgent2, {})
    ]
    dm_types = [
        (ThompsonMultiArmedBanditManager, {}),
        (UCB1TunedMultiArmedBanditManager, {}),
        (MultiArmedBanditManager, {}),
        
        (ProvideMissingManager, {}),
        
        # ---- Baselines ----
        (OracleAllManager, {}),
        (RandomManager, {}),
        
        # ---- Extra Tests, not included in the graphs ----
        # (UCB1MultiArmedBanditManager, {}),
        # (MultiArmedBanditManager, {"epsilon": .05}),
        # (MultiArmedBanditManager, {"epsilon": .1}),
        # (MultiArmedBanditManager, {"epsilon": .3}),
        # (DecayMultiArmedBanditManager, {}),
    
    ]

    # load the distractions
    with open("distraction_gen/distraction_gen_info/distraction.json", "r") as fp:
        distractions = json.load(fp, cls=DistractionsDecoder)

    # set up the environment
    CatWorldEnv.load_distractions(distractions)
    
    for pre_pref, pre_name, pre_action_type in all_modes_iterator():
        # generate the first 90 steps, and save them
        # todo: figure out how to reuse just in case we need to.
        # todone
        # pre_history_path, pre_pref_path, _ = backgen_90_history(pre_pref, pre_name)
        
        # run actual tests
        for post_pref, post_name, post_action_type in all_modes_iterator(skip=pre_action_type):
            # load up the first 90 steps, generate 10 more of the post_pref
            # todo: figure out how to reuse just in case we need to
            # todone
            # post_history_path, post_pref_path, mode_name = backgen_10_history(pre_history_path, pre_pref_path, pre_name, post_pref, post_name)
            post_history_path, post_pref_path, mode_name = load_all_history(pre_name, post_name)
            
            # collect data from each agent and manager
            for agent_type, agent_kwargs in agent_types:
                for dm_type, dm_kwargs in dm_types:
                    collect_data(
                        trials=trials,
                        agent_type=agent_type,
                        agent_kwargs=agent_kwargs,
                        dm_type=dm_type,
                        dm_kwargs=dm_kwargs,
                        max_turn_count=max_turn_count,
                        scene_num=mode_name,
                        history_file=post_history_path,
                        pref_file=post_pref_path,
                    )
            pass
    pass


if __name__ == '__main__':
    main_all_scenarios()
