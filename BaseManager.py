import copy
import itertools
import os

import json
import random
from collections import defaultdict

import numpy as np

import CatWorldEnv
from CatWorldEnv import GameState, env_compat_layer, GameStateJSONEncoder, random_argmax_from_dict, random_argmin_from_dict
from BaseAgent import BaseAgent


# the base class manager, the do nothing manager
class BaseManager:
    # json is slow and bad, unless I need to manually explore the data, this should be off
    save_json: bool = False
    preference_action_types: list = []
    long_name: str = "Do-Nothing Manager"
    
    def __init__(self, env, requested_infos):
        self.player_model = {action_type: 1 for action_type in self.preference_action_types}
        
        # env allows for directly sending a command, requested info is for processing the output (arguably should make our own with full permissions)
        self.env = env
        self.requested_infos = requested_infos
        
        self.distraction_needed = False
        self.action_history = []
        # what is the maximum amount of turns that the manager looks at
        self.max_history_length = 200
        # what turn does the experience manager start paying attention to
        self.start_history_turn = 90
        
        self.num_rounds = 0
        self.last_distractions = []
        self.last_action_types = []
        # the fake ones help when we pretend to add a distraction, but just reuse something existing in the environment instead
        self.fake_last_distractions = []
        self.fake_last_action_types = []
        
        # for each entry: [number of times a distraction is interacted with, number of times a distraction is given]
        self.interactions = {action_type: [0, 0] for action_type in self.preference_action_types}
        
        # recording
        self.player_pref_record = []
        self.player_model_record = []
        self.action_dist_record = []
        self.interactions_record = []
        self.distraction_record = []
        
        self.save_output = True
        
        # for differentiating between changed args like max history length and epsilon for MABM
        self.name_addendum = []
    
    def action(self, obs, infos, old_infos, done):
        action_types = self.select_action_type(infos)
        
        if action_types is None or len(action_types) == 0:
            return obs, infos, old_infos, done

        # convert the list to a string
        action_types_str = " ".join(action_types)
        command = f"dm spawn distraction temp {action_types_str}"
        obs, infos, old_infos, done = self.send_command(command, infos)
        self.record_last_distraction(infos, old_infos, action_types)
        
        return obs, infos, old_infos, done
    
    def select_action_type(self, infos):
        return []
    
    def random_action_type(self):
        return random.choice(list(self.interactions.keys()))
    
    def observation(self, command, infos, agent: BaseAgent):
        # update distraction interactions
        self.update_interactions(infos)
        
        # increase number of rounds
        self.num_rounds += 1
        
        # record action
        self.record_action(command, infos)
        # record internal player model
        self.player_model_record.append(copy.deepcopy(self.player_model))
        # record action history player model
        self.action_dist_record.append(self.summarize_action_history())
        # record the players actual preferences
        self.player_pref_record.append(copy.deepcopy(agent.preferred_actions))
        # record what the players interactions with distractions (slight misnomer) at this step
        self.interactions_record.append(copy.deepcopy(self.interactions))
        
        # record last distraction
        self.distraction_record.append(copy.deepcopy(self.last_distractions))
        pass
    
    def update_interactions(self, infos):
        action_type = CatWorldEnv.action_to_type[infos.action["verb"]]
        
        # record if agent interacts with the distraction
        last_distractions = self.last_distractions + self.fake_last_distractions
        last_action_types = self.last_action_types + self.fake_last_action_types
        
        # if action_type in self.last_action_types:
        if (infos.action["subject"] in last_distractions or infos.action["object"] in last_distractions) and action_type in last_action_types:
            self.interactions[action_type][0] += 1
        # record number of times distraction given
        for last_action_type in last_action_types:
            self.interactions[last_action_type][1] += 1
    
    def send_command(self, command, old_infos):
        obs, score, done, infos = self.env.step(command)
        obs, infos, old_infos, done = env_compat_layer(obs, old_infos, self.requested_infos)
        return obs, infos, old_infos, done
    
    def output_data(self, base_folder, trial=None, agent_name=None, scene_num=None):
        if agent_name is None:
            agent_name = ""
        if trial is None:
            trial = ""
        if scene_num is None:
            scene_num = "all"
            
        folder = f"{base_folder}/{scene_num}"
        
        data = {
            "player_model_record": self.player_model_record,
            "action_dist_record": self.action_dist_record,
            "player_pref_record": self.player_pref_record,
            "interactions_record": self.interactions_record,
            "action_history": self.action_history,
            "distraction_record": self.distraction_record,
        }
        name = f"{self.short_name()}{'+' if str(agent_name) else ''}{agent_name}"
        save_path = None
        if self.save_output:
            # ensure directory existence
            path_dir = f"{folder}/{name}/raw"
            if not os.path.exists(path_dir):
                os.makedirs(path_dir)

            # write the data to file
            if self.save_json:
                save_path = f"{path_dir}/{trial}.json"
                with open(save_path, "w") as fp:
                    json.dump(data, fp, cls=GameStateJSONEncoder)
                pass
            else:
                save_path = f"{path_dir}/{trial}.npy"
                np.save(save_path, data)
        return data, name, save_path
    
    # region action history
    # load the static backhistory from file
    def load_backhistory(self, backhistory_file):
        # load file
        if self.save_json:
            with open(backhistory_file, "r") as fp:
                data: dict = json.load(fp)
        else:
            data: dict = np.load(backhistory_file, allow_pickle=True).item()
            
        # overwrite the current history
        self.player_model_record = data["player_model_record"]
        self.action_dist_record = data["action_dist_record"]
        self.player_pref_record = data["player_pref_record"]
        self.interactions_record = data["interactions_record"]
        self.action_history = data["action_history"]
        self.distraction_record = data["distraction_record"]
        
        return self.action_history
    
    def summarize_action_history(self):
        action_counts = {action_type: 1 for action_type in self.preference_action_types}
        cut_action_history = copy.deepcopy(self.action_history)
        
        # cut down the action history to only start at self.start_history_turn
        if len(cut_action_history) > self.start_history_turn:
            cut_action_history = cut_action_history[self.start_history_turn:]
        
        # cut down the action history to be self.max_history_length
        if len(cut_action_history) > self.max_history_length:
            cut_action_history = cut_action_history[-self.max_history_length:]
        
        for command, infos in cut_action_history:
            # figure out what type of action it is
            action_verb = infos["action"]["verb"]
            action_type = CatWorldEnv.action_to_type[action_verb]
            
            # add to that corresponding count
            if action_type in action_counts.keys():
                action_counts[action_type] += 1
            
            # find which actions are available on this turn, and calculate the probability for any random one to be chosen
            # todo: perhaps change this to only look at whether a action type was offered rather than how many offerings there are of each?
            # available_distribution = {action: len(action_list) + 1 for action, action_list in infos.commands_by_type.items() if action != "move"}
            # available_distribution = {action: count / sum(available_distribution.values()) for action, count in available_distribution.items()}
            
            # available_counts = {action: count + available_distribution[action] for action, count in available_counts.items()}
            
            # todo: given the available distribution, what is the likelihood that the action taken was due to want vs availability
            #  we just want that actions that are more available have less influence because its more likely that they were chosen due to just being there
            pass
        
        # normalize
        action_distribution = {action: value / sum(action_counts.values()) for action, value in action_counts.items()}
        # print(self.action_history[-1][1]["action"])
        # if len(self.action_history) > 10:
        #     pprint(action_distribution)
        #     print(end="")
        return action_distribution
    
    def validate_command(self, command, infos):
        # todo: look into the infos to see if we have an error state
        return bool(self)
    
    def record_action(self, command, infos):
        if self.validate_command(command, infos):
            infos.set_dm_model(self.player_model)
            self.action_history.append((command, infos))
    
    def record_last_distraction(self, infos, old_infos, action_types):
        if "each" in action_types:
            action_types = list(self.player_model.keys())
        # update what our last spawned distraction is for the observations
        old_distractions = old_infos["distractions"]
        new_distractions = infos["distractions"]
        self.last_distractions = list(set(new_distractions) - set(old_distractions))
        self.last_action_types = action_types
    
    # endregion
    
    # region player model
    @property
    def player_model(self):
        return self._player_model
    
    @player_model.setter
    def player_model(self, action_dist):
        normalize = sum(action_dist.values())
        self._player_model = {action: dist / normalize for action, dist in action_dist.items()}
    # endregion
    
    def short_name(self):
        abbreviation = "".join(i for i in type(self).__name__ if not i.islower())
        arg_changes = "-".join(f"{''.join(s[0] for s in key.split('_'))},{arg}" for key, arg in self.name_addendum)
        return f"{abbreviation}{'-' if arg_changes else ''}{arg_changes}"


# this one just randomly chooses a distraction
class RandomManager(BaseManager):
    long_name: str = "Random Manager"
    
    def select_action_type(self, infos):
        return [self.random_action_type()]


# this one cheats and knows what the agent's insides look like
class OracleKnowledgeManager(BaseManager):
    long_name: str = "Oracle Knowledge Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        # this is representing the agents preferred action,
        self.preferred_actions = None

    def observation(self, command, infos, agent: BaseAgent):
        super().observation(command, infos, agent)
        self.preferred_actions = agent.preferred_actions
    
    def select_action_type(self, infos):
        # always give agent a random distraction in accordance to the agents own model
        if self.preferred_actions is None:
            return [self.random_action_type()]
        else:
            return random.choices(list(self.preferred_actions.keys()), weights=list(self.preferred_actions.values()))


# this one cheats and knows what the agent's insides look like
class OracleBestManager(BaseManager):
    long_name: str = "Oracle Best Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        # this is representing the agents preferred action,
        self.preferred_actions = None

    def observation(self, command, infos, agent: BaseAgent):
        super().observation(command, infos, agent)
        self.preferred_actions = agent.preferred_actions
    
    def select_action_type(self, infos):
        # always give agent a random distraction in accordance to the agents own model
        if self.preferred_actions is None:
            return [self.random_action_type()]
        else:
            return [random_argmax_from_dict(self.preferred_actions)]
    

# this one cheats and sends one of each distractions, its a special case so it overrides action instead of select_action_type
class OracleAllManager(BaseManager):
    long_name: str = "One-Of-Each Manager"
    
    def select_action_type(self, infos):
        return ["each"]


# this one cheats kinda. it looks at the environment and only adds a distraction for whatever is missing in the environment
class ProvideMissingManager(BaseManager):
    long_name: str = "Provide-Missing Manager"
    
    def select_action_type(self, infos):
        # find the lowest amount of each of the commands
        command_counts = {command_type: len(commands) for command_type, commands in infos.commands.items() if command_type != "move"}
        return [random_argmin_from_dict(command_counts)]
        
        
class KnowledgeMissingManager(BaseManager):
    long_name: str = "Knowledge Missing Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        # this is representing the agents preferred action,
        self.knowledge = []
        
    # override the observation to add the ability to see if the agent interacted with stuff.
    def observation(self, command, infos, agent: BaseAgent):
        # record the regular observation
        super().observation(command, infos, agent)
        
        # record our special observation
        # consider the recent history and see if the agent interacted with any distractions
        distractions_acted = []
        
        # cut the history down to size
        if len(self.action_history) > self.max_history_length:
            cut_action_history = self.action_history[-self.max_history_length:]
        else:
            cut_action_history = self.action_history
            
        # search for distraction actions
        for _, past_infos in cut_action_history:
            past_infos = GameState(past_infos)
            if past_infos.variables["distracted"]:
                action_verb = past_infos["action"]["verb"]
                action_type = CatWorldEnv.action_to_type[action_verb]
                distractions_acted.append(action_type)
        
        # record them
        self.knowledge = distractions_acted
    
    def select_action_type(self, infos):
        # find the lowest amount of each of the commands
        command_counts = {command_type: len(commands) for command_type, commands in infos.commands.items() if command_type != "move"}
        
        # if there is a tie, break it with knowledge
        min_commands = [command for command, count in command_counts.items() if count == min(command_counts.values())]
        min_command_counts = {command: self.knowledge.count(command) for command in min_commands}
        
        return [random_argmin_from_dict(min_command_counts)]


class AllActionKnowledgeMissingManager(KnowledgeMissingManager):
    long_name: str = "AA Knowledge Missing Manager"
    
    def observation(self, command, infos, agent: BaseAgent):
        super().observation(command, infos, agent)
        distractions_acted = []
        
        # cut the history down to size
        if len(self.action_history) > self.max_history_length:
            cut_action_history = self.action_history[-self.max_history_length:]
        else:
            cut_action_history = self.action_history
            
        # search for distraction actions
        for _, past_infos in cut_action_history:
            action_verb = past_infos["action"]["verb"]
            action_type = CatWorldEnv.action_to_type[action_verb]
            distractions_acted.append(action_type)
        
        # record them
        self.knowledge = distractions_acted
        
        
class IterativeAllManager(BaseManager):
    long_name: str = "Iterative-All Manager"
    
    def select_action_type(self, infos):
        return [list(self.interactions)[self.num_rounds % len(self.interactions)]]
    
    
class IterativeRandomManager(BaseManager):
    long_name: str = "Iterative Random Manager"
    
    def select_action_type(self, infos):
        return [random_argmin_from_dict({action_type: d for action_type, (n, d) in self.interactions.items()})]
    
        
# the base MAB manager, implementing epsilon greedy?
class MultiArmedBanditManager(BaseManager):
    long_name: str = "ε-Greedy Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        self.epsilon = 0.2
    
    def select_action_type(self, infos):
        # decide whether or not to do an explore or exploit turn
        if random.random() < self.epsilon:
            # pick at random
            action_type = random.choice(list(self.interactions.keys()))
        else:
            # pick the best one so far
            action_rewards = {action_type: (n+1)/(d+1) for action_type, (n, d) in self.interactions.items()}
            action_type = random_argmax_from_dict(action_rewards)
        return [action_type]


class DecayMultiArmedBanditManager(MultiArmedBanditManager):
    long_name: str = "ε-Decay Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        self.max_epsilon = 1
        self.decay_shift = 0
    
    @property
    def epsilon(self):
        # decrease the epsilon based on number of interactions
        return self.max_epsilon/(self.num_rounds + 1 + self.decay_shift)
    
    @epsilon.setter
    def epsilon(self, epsilon):
        self._epsilon = epsilon
        return
    

# thanks to https://towardsdatascience.com/multi-armed-bandits-upper-confidence-bound-algorithms-with-python-code-a977728f0e2d
class UCB1MultiArmedBanditManager(MultiArmedBanditManager):
    long_name: str = "UCB1 Manager"
    
    @staticmethod
    def sample_mean(interactions):
        n = np.sum(interactions)
        return interactions[0] / n
    
    def C(self, interactions):
        N = self.num_rounds
        n = np.sum(interactions)
        return np.sqrt(2*np.log(N) / n)
    
    def select_action_type(self, infos):
        # first play all one of each (aka wait till our observation includes at least one of each)
        if sum(interactions[1] for action_type, interactions in self.interactions.items()) < len(self.interactions):
            action_rewards = {action_type: np.sum(interactions) for action_type, interactions in self.interactions.items()}
            action_type = random_argmin_from_dict(action_rewards)
        else:
            # calculate upper confidence bound?
            UCI = {action_type: self.sample_mean(interactions) + self.C(interactions) for action_type, interactions in self.interactions.items()}
            action_type = random_argmax_from_dict(UCI)
            
        return [action_type]
    pass


# better than UCB1-normal apparently
class UCB1TunedMultiArmedBanditManager(UCB1MultiArmedBanditManager):
    long_name: str = "UCB1-Tuned Manager"
    
    def C(self, interactions):
        N = self.num_rounds
        n = np.sum(interactions)
        return np.sqrt(2*np.log(N) / n) * np.minimum(1/4, self.V(interactions))
    
    def V(self, interactions):
        N = self.num_rounds
        n = np.sum(interactions)
        rewards_sum = interactions[0]
        avg_reward = rewards_sum / n
        # the square of the reward over n - the square of the average reward + that last part
        return (np.square(rewards_sum) / n) - np.square(avg_reward) + np.sqrt(2*np.log(N) / n)
    pass


class ThompsonMultiArmedBanditManager(MultiArmedBanditManager):
    long_name: str = "Thompson Manager"
    
    @staticmethod
    def sample_distraction_mean(interactions):
        # + 1 for a Beta(1, 1) prior
        successes = interactions[0] + 1
        failures = interactions[1] - interactions[0] + 1
        return np.random.beta(a=successes, b=failures, size=1)[0]
    
    def select_action_type(self, infos):
        # implement thompson sampling
        samples = {action_type: self.sample_distraction_mean(interactions) for action_type, interactions in self.interactions.items()}
        action_type = random_argmax_from_dict(samples)
            
        return [action_type]
    pass


class MultiMultiArmedBanditManager(BaseManager):
    long_name: str = "2 Arm ε-Greedy Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        self.epsilon = 0.2
    
    def select_action_type(self, infos):
        # decide whether or not to do an explore or exploit turn
        if random.random() < self.epsilon:
            # pick 2 at random
            action_types = random.sample(list(self.interactions.keys()), k=2)
        else:
            # pick the best 2 so far
            action_rewards = {action_type: (n+1)/(d+1) for action_type, (n, d) in self.interactions.items()}
            action_type1 = random_argmax_from_dict(action_rewards)
            # remove action type 1 from the possible choices and choose another
            del action_rewards[action_type1]
            action_type2 = random_argmax_from_dict(action_rewards)
            action_types = [action_type1, action_type2]
            pass
        return action_types
    
    
class BatchedMultiArmedBanditManager(BaseManager):
    long_name: str = "up to 2 Arm ε-Greedy Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        self.epsilon = 0.2
        
        self.max_batch_size = 2
        batched_interactions = {tuple(sorted(batch)): [0, 0] for batch in itertools.combinations(self.interactions.keys(), self.max_batch_size)}
        regular_interactions = {(k,): [0, 0] for k in self.interactions.keys()}
        self.extra_interactions = defaultdict(lambda: [0, 0], {**batched_interactions, **regular_interactions})
        
    def update_interactions(self, infos):
        # update as normal for stats calculation
        super().update_interactions(infos)
        
        # update our special self.extra_interactions which contains action pairs along with regular interactions
        action_type = CatWorldEnv.action_to_type[infos.action["verb"]]
        batched_action_types = tuple(sorted(self.last_action_types))
        # multi_action_discount = len(self.last_action_types)
        if (infos.action["subject"] in self.last_distractions or infos.action["object"] in self.last_distractions) and action_type in self.last_action_types:
            self.extra_interactions[batched_action_types][0] += 1
        self.extra_interactions[batched_action_types][1] += 1
        pass
    
    def select_action_type(self, infos):
        # decide whether or not to do an explore or exploit turn
        if random.random() < self.epsilon:
            # pick at random, up to self.max_batch_size
            k = random.randint(1, self.max_batch_size)
            action_types = random.sample(list(self.interactions.keys()), k=k)
        else:
            # pick the best one so far
            action_rewards = {action_type: (n+1)/(d+1) for action_type, (n, d) in self.extra_interactions.items()}
            action_types = list(random_argmax_from_dict(action_rewards))
        return action_types
    
    
class SharedBatchedMABManager(BaseManager):
    long_name: str = "Shared Batched ε-Greedy Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        self.epsilon = 0.2
        
        self.max_batch_size = 2
        batched_interactions = {tuple(sorted(batch)): [0, 0] for batch in itertools.combinations(self.interactions.keys(), self.max_batch_size)}
        regular_interactions = {(k,): [0, 0] for k in self.interactions.keys()}
        self.extra_interactions = defaultdict(lambda: [0, 0], {**batched_interactions, **regular_interactions})
        
    def update_interactions(self, infos):
        # update as normal for stats calculation
        super().update_interactions(infos)
        
        # recalculate our special self.extra_interactions which contains action pairs along with regular interactions
        # we do this by looking at the interactions and just copying them over, as if everything was just fine
        # list of interaction keys
        interaction_keys = list(self.interactions.keys())
        batched_interactions = {
            tuple(sorted([key1, key2])):
                [(self.interactions[key1][0] + self.interactions[key2][0])/2, (self.interactions[key1][1] + self.interactions[key2][1])/2]
            for i, key1 in enumerate(interaction_keys)
            for key2 in interaction_keys[i + 1:]
        }
        regular_interactions = {(k,): v for k, v in self.interactions.items()}
        self.extra_interactions = {**batched_interactions, **regular_interactions}
    
    def select_action_type(self, infos):
        if random.random() < self.epsilon:
            # pick at random, up to self.max_batch_size
            k = random.randint(1, self.max_batch_size)
            action_types = random.sample(list(self.interactions.keys()), k=k)
        else:
            # pick the best one so far
            action_rewards = {action_type: (n+1)/(d+1) for action_type, (n, d) in self.extra_interactions.items()}
            action_types = list(random_argmax_from_dict(action_rewards))
        return action_types


class SharedUCB1TunedMABManager(UCB1TunedMultiArmedBanditManager, SharedBatchedMABManager):
    long_name: str = "Shared Batched UCB1-Tuned Manager"
    
    def select_action_type(self, infos):
        # first play all one of each (aka wait till our observation includes at least one of each)
        if sum(interactions[1] for action_type, interactions in self.interactions.items()) < len(self.interactions):
            action_rewards = {action_type: np.sum(interactions) for action_type, interactions in self.interactions.items()}
            action_type = [random_argmin_from_dict(action_rewards)]
        else:
            # calculate upper confidence bound?
            UCI = {action_type: self.sample_mean(interactions) + self.C(interactions) for action_type, interactions in self.extra_interactions.items()}
            action_type = list(random_argmax_from_dict(UCI))

        return action_type
    pass


class ProvideMissingMABManager(BaseManager):
    long_name: str = "Provide Missing ε-Greedy Manager"
    
    def __init__(self, env, requested_infos):
        super().__init__(env, requested_infos)
        self.epsilon = 0.2
        
    def amend_action_types(self, infos, action_types):
        # build a list of action types not present in the current room
        existing_action_types = [command_type for command_type, commands in infos.commands.items() if command_type != "move" and len(commands) != 0]
        
        # if our action types include something from existing ones, then we can remove those, and just pretend that we pulled that arm.
        new_action_types = []
        self.fake_last_action_types = []
        self.fake_last_distractions = []
        for action_type in action_types:
            if action_type not in existing_action_types:
                new_action_types.append(action_type)
            else:
                self.fake_last_action_types.append(action_type)
                # find all subjects that are of type action_type within the game
                subjects = [command.sub for command in infos.commands[action_type] if command.sub != ""]
                # objects = [command.obj for command in infos.commands[action_type] if command.obj != ""]
                self.fake_last_distractions += subjects
                
        return new_action_types
    
    def select_action_type(self, infos):
        # decide whether or not to do an explore or exploit turn
        if random.random() < self.epsilon:
            # pick at random
            action_type = random.choice(list(self.interactions.keys()))
        else:
            # pick the best one so far
            action_rewards = {action_type: (n + 1) / (d + 1) for action_type, (n, d) in self.interactions.items()}
            action_type = random_argmax_from_dict(action_rewards)
        
        action_types = self.amend_action_types(infos, [action_type])
        
        return action_types
    
    
if __name__ == '__main__':
    pass
