import time

import gym
import textworld.gym

from tqdm import trange

import generate_preference_distributions
from BaseManager import *
from BaseAgent import *

import CatWorldEnv
from CatWorldEnv import env_compat_layer
from datetime import datetime

from generate_inform_extension import DistractionsDecoder

basic_infos = ["admissible_commands", "entities", "location", "facts"]
game_file = "Inform7 projects/text world doubt.inform/Build/output.ulx"
g_max_turn_count = 100
g_backhistory_file = "ExperienceManager_current"

data_dir = "output_data"
curr_date_dir = datetime.now().date()

tqdm_args = {
    "ncols": 150,
    "position": 0
}


# region game stuff
def apply_kwargs(obj, kwargs):
    if kwargs is None:
        return
    for key, arg in kwargs.items():
        if key in obj.__dict__:
            obj.__dict__[key] = arg
            obj.name_addendum.append((key, arg))
        else:
            print(f"invalid arg: {key} -> {arg}, continuing")
        
        
# todo: change the game into a GameClass which can handle setup, init, and play. this is getting out of hand.
#   alternatively, figure out how to better batch these?
def set_up_game(agent_type=None, dm_type=None, max_turn_count=g_max_turn_count, agent_kwargs=None, dm_kwargs=None):
    # load the distractions
    with open("distraction_gen/distraction_gen_info/distraction.json", "r") as fp:
        distractions = json.load(fp, cls=DistractionsDecoder)
    
    # set up the environment
    CatWorldEnv.load_distractions(distractions)
    # make sure to remove the move action as it is not a valid preference
    preference_action_types = [action for action in CatWorldEnv.type_to_action.keys() if action != "move"]
    
    # set up agent
    BaseAgent.preference_action_types = preference_action_types
    if agent_type is None:
        # agent = RandomAvailableAgent()
        # agent = PolicyAgent()
        agent = SimplePreferenceAgent()
    else:
        agent = agent_type()

    extra_info = {**{i: True for i in basic_infos}, **agent.required_info}
    requested_infos = textworld.EnvInfos(**extra_info)

    # use double max_turn_count because currently injected distractions count towards this count.
    env_id = textworld.gym.register_game(game_file, requested_infos, max_episode_steps=max_turn_count * 3)
    env = gym.make(env_id)

    # set up drama manager
    BaseManager.preference_action_types = preference_action_types
    if dm_type is None:
        dm = RandomManager(env, requested_infos)
        # dm = ExperienceManager(env, requested_infos)
    else:
        dm = dm_type(env, requested_infos)
        
    apply_kwargs(agent, agent_kwargs)
    apply_kwargs(dm, dm_kwargs)

    return dm, agent, env, requested_infos


def initialize_game(env, requested_infos):
    # reset env and variables
    obs, infos = env.reset()
    score = 0

    # get first observation
    obs, infos, old_infos, done = env_compat_layer(obs, {}, requested_infos)
    return obs, infos, old_infos, done, score


def process_command(env, command, old_infos, requested_infos, render_text):
    if render_text:
        print(f"> {command}")

    # process the command
    obs, score, done, infos = env.step(command)

    # process the new info
    obs, infos, old_infos, done = env_compat_layer(obs, old_infos, requested_infos)
    return obs, infos, old_infos, done


def game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=True, max_turn_count=g_max_turn_count):
    # print initial observation
    if render_text:
        print(obs)
    
    turn_count = 1
    while not (done or turn_count > max_turn_count):
        # dm updates these values and may take a single action
        obs, infos, old_infos, done = dm.action(obs, infos, old_infos, done)
        
        # Agents turn
        # command = input("> ")
        command = agent.act(infos, score, done)
        
        # todo: implement error recognition and signaling in inform7
        #  extract error state to figure out whether an action should be recorded
        #  and if we need to do other stuff
        #  This should probably be done within the env_compat_layer
        #  Note that this is still not done, currently no action that the agents take result in error but this is Still Not Done ~~ and also old infos is mildly corrupted by the DM
        obs, infos, old_infos, done = process_command(env, command, old_infos, requested_infos, render_text)
        
        # allow the dm and the agent to observe the results
        dm.observation(command, infos, agent)
        agent.observation_record(command, infos)
        
        turn_count += 1
        
        if render_text:
            print(obs)
        
        # we need the old infos just in case there is a problem on the inform side of things like it asks for clarification or something.
        old_infos = infos
    if render_text:
        print(f"your quest is over! in {turn_count} turns")


def collect_data(trials=10, agent_type=None, dm_type=None, agent_kwargs=None, dm_kwargs=None, max_turn_count=g_max_turn_count, scene_num=None, history_file=None, pref_file=None):
    # add some timing for performance metrics
    time_it()
    
    # just in case, a data backup method of sorts
    base_folder = f"{data_dir}/{curr_date_dir}"
    
    # generate all the data
    for trial in trange(trials, bar_format='{l_bar}{bar}| ' + f"{dm_type.__name__}+{agent_type.__name__}-{scene_num}", **tqdm_args):
        trial = str(trial)
        
        # set up the game
        dm, agent, env, requested_infos = set_up_game(agent_type=agent_type, dm_type=dm_type, agent_kwargs=agent_kwargs, dm_kwargs=dm_kwargs)
        obs, infos, old_infos, done, score = initialize_game(env, requested_infos)
        dm.save_output = True
        
        # these files are now mandatory, cuz not having them causes too much issues.
        if pref_file is None or history_file is None:
            raise FileNotFoundError
        
        # load the correct back history
        action_history = dm.load_backhistory(history_file)
        # set our agent's preferences to match
        agent.preferred_actions = generate_preference_distributions.load_mode_file(pref_file)
        
        # copy over the action history to the agent.
        agent.action_history = copy.deepcopy(action_history)
        
        # do the actual game
        game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=False, max_turn_count=max_turn_count)
    
        # extract the data for processing and save it
        data, name, save_path = dm.output_data(
            base_folder=base_folder,
            trial=trial,
            agent_name=agent.short_name(),
            scene_num=scene_num
        )

        # save some of the parameters used for this test
        parameter_info = {
            "trials": trials,
            "agent_name": agent_type.long_name,
            "dm_name": dm_type.long_name,
            "scene_num": scene_num,
            "initial_pref": generate_preference_distributions.load_mode("history"),
            "scene_pref": generate_preference_distributions.load_mode(scene_num),
            "dm_details": dm_kwargs,
            "agent_details": agent_kwargs,
        }
        with open(f"{base_folder}/{scene_num}/{name}/params.json", "w") as fp:
            json.dump(parameter_info, fp)
# endregion


# region mains
def main(test_mode=None):
    trials = 30
    max_turn_count = g_max_turn_count
    agent_types = [
        (SimplePreferenceAgent, {}),
        (SaliencyAgent, {}),
        # (SimpleSaliencyAgent, {}),
        # (FlatSaliencyAgent, {}),
        (MovePrefAgent, {}),
        # (MovePrefSaliencyAgent, {}),
    ]
    dm_types = [
        # (ThompsonMultiArmedBanditManager, {}),
        # (ThompsonMultiArmedBanditManager, {"max_history_length": 20}),
        
        # (UCB1TunedMultiArmedBanditManager, {}),
        # (UCB1TunedMultiArmedBanditManager, {"max_history_length": 20}),
        
        # (UCB1MultiArmedBanditManager, {}),
        # (UCB1MultiArmedBanditManager, {"max_history_length": 20}),
        
        # (DecayMultiArmedBanditManager, {}),
        # (DecayMultiArmedBanditManager, {"max_history_length": 20}),
        
        # (MultiArmedBanditManager, {"epsilon": .05}),
        # (MultiArmedBanditManager, {}),
        # (MultiArmedBanditManager, {"max_history_length": 20}),
        # (MultiArmedBanditManager, {"epsilon": .2}),
        
        # (OracleKnowledgeManager, {}),
        # (ProvideMissingManager, {}),
        # (KnowledgeMissingManager, {}),
        # (AllActionKnowledgeMissingManager, {}),
        
        # -- Strange Stuff --
        # (MultiMultiArmedBanditManager, {}),
        # (BatchedMultiArmedBanditManager, {}),
        # (SharedBatchedMABManager, {}),
        # (SharedUCB1TunedMABManager, {}),
        # (ProvideMissingMABManager, {}),
        
        # ---- Baselines ----
        (OracleAllManager, {}),
        # (OracleAllManager, {"max_history_length": 20}),
        # (OracleBestManager, {}),
        (RandomManager, {}),
        # (BaselineManager, {"max_history_length": 20}),
        # (IterativeAllManager, {}),
        # (IterativeRandomManager, {}),
        # (BaseManager, {}),
        
    ]
    skip_redo_history = False
    
    # there is enough trouble with back history, and it is so cheap to run that we might as well just always run it for each test
    # though skipping is enabled for the sake of rerunning a test on the same directory (no way to automatically detect this yet)
    if not skip_redo_history:
        before_history_path, after_history_path, before_pref_path, after_pref_path = backgen_modal_history(test_mode_testing)
    else:
        before_history_path = f'backhistory/{test_mode}/BM/raw/pref-before.npy'
        after_history_path = f'backhistory/{test_mode}/BM/raw/pref-after.npy'
        before_pref_path = f'backhistory/history/preference_dist.json'
        after_pref_path = f'backhistory/{test_mode}/preference_dist.json'
    
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
                scene_num=test_mode,
                history_file=after_history_path,
                pref_file=after_pref_path,
            )
    pass


def main2():
    test_mode = "look2touch"
    # set up the game
    dm, agent, env, requested_infos = set_up_game(agent_type=MovePrefAgent2, dm_type=OracleAllManager)
    obs, infos, old_infos, done, score = initialize_game(env, requested_infos)
    
    # load the static history
    if test_mode is not None:
        # load the correct back history
        agent.action_history = dm.load_backhistory(f"backhistory/{test_mode}/BM/raw/pref-after.npy")
        # set our agent's preferences to match
        agent.preferred_actions = generate_preference_distributions.load_mode(test_mode)
    
    # do the actual game
    game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=True, max_turn_count=100)
    
    breakpoint()
    exit()
# endregion


# region debug and gen
def backgen_modal_history(test_mode=None):
    time_it()
    # set up the game, using the regular manager because it does nothing
    dm, agent, env, requested_infos = set_up_game(dm_type=BaseManager)
    obs, infos, old_infos, done, score = initialize_game(env, requested_infos)
    dm.save_output = True
    
    # generate 90 turns of gameplay with pre pref model
    # todo: using the static gen_mode, which is not suitable after the paper since the names might change. It is set like this for now for consistency.
    agent.preferred_actions, before_pref_path = generate_preference_distributions.gen_mode_static("history")
    game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=False, max_turn_count=90)
    _, _, before_history_path = dm.output_data("backhistory", "pref-before", scene_num=test_mode)
    
    # generate 10 turns of gameplay with post pref model
    # todo: likewise
    agent.preferred_actions, after_pref_path = generate_preference_distributions.gen_mode_static(test_mode)
    game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score, render_text=False, max_turn_count=10)
    _, _, after_history_path = dm.output_data("backhistory", "pref-after", scene_num=test_mode)
    
    return before_history_path, after_history_path, before_pref_path, after_pref_path
    

def play_game():
    dm, agent, env, requested_infos = set_up_game(agent_type=HumanAgent)
    obs, infos, old_infos, done, score = initialize_game(env, requested_infos)
    
    # turn off any output saving
    dm.save_output = False
    
    game_loop(dm, agent, env, requested_infos, obs, infos, old_infos, done, score)
    
    
time_it_list = []


def time_it():
    global time_it_list
    time_it_list.append(time.time())
    if len(time_it_list) == 1:
        print("starting timer")
    else:
        total = format_time(time_it_list[-1] - time_it_list[0])
        lap = format_time(time_it_list[-1] - time_it_list[-2])
        print(f"Total: {total} - Lap: {lap}")
        
        
def format_time(t):
    t = int(t)
    h = t // (60*60)
    t = t % (60*60)
    m = t // 60
    s = t % 60
    return f"{h:02}:{m:02}:{s:02}"
    
    
# endregion


if os.name == 'nt':
    print("Run this only under wsl or linux")
    exit()


if __name__ == '__main__':
    main2()
    # play_game()
    
    # for test_mode_testing in [0, 1, 2]:
    #     main(test_mode_testing)
    #     pass
    # time_it()
