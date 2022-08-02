import abc
import math
import random
import statistics
from collections import defaultdict

import textworld

from CatWorldEnv import GameState, random_argmax_from_dict, random_argmin_from_dict


class BaseAgent(textworld.Agent, abc.ABC):
    long_name: str = "Random Agent"
    
    preference_action_types: list = []
    required_info = {
    }
    
    def __init__(self):
        # the preferred actions can be changed later, before the start of the game, but needs a default value for now
        self.preferred_actions = {action_type: 1 for action_type in self.preference_action_types if action_type != "move"}
        
        self.move_chance = 0.1
        self.action_history = []

        # for differentiating between changed args like move_chance
        self.name_addendum = []
        
        super().__init__()
    
    @abc.abstractmethod
    def act(self, game_state: GameState, reward, done):
        return str(random.choice(game_state.admissible_commands))
    
    def act_wander(self, game_state: GameState):
        return str(random.choice(game_state.commands_by_type["move"]))
    
    def act_goal(self, game_state: GameState):
        if game_state.next_action:
            return game_state.next_action
        return self.act_wander(game_state)
    
    # region action preference
    @property
    def preferred_actions(self):
        return self._preferred_actions
    
    @preferred_actions.setter
    def preferred_actions(self, action_dist):
        normalize = sum(action_dist.values())
        self._preferred_actions = {action: dist / normalize for action, dist in action_dist.items()}
    
    # simple method to add to the preferred_actions. adding only one will cause the rest to decrease.
    def adjust_preferred_action(self, action_adjustment):
        action_adjustment = defaultdict(lambda: statistics.mean(action_adjustment.values()), action_adjustment)
        self.preferred_actions = {action: preference + action_adjustment[action] for action, preference in self.preferred_actions.items() if action != "move"}
    
    def observation_record(self, command, infos):
        # record action
        self.record_action(command, infos)
    
    def validate_command(self, command, infos):
        # todo: look into the infos to see if we have an error state
        return bool(self)
    
    def record_action(self, command, infos):
        if self.validate_command(command, infos):
            self.action_history.append((command, infos))
    # endregion
    
    def short_name(self):
        abbreviation = "".join(i for i in type(self).__name__ if i.isupper())
        arg_changes = "-".join(f"{key[0]},{arg}" for key, arg in self.name_addendum)
        return f"{abbreviation}{'-' if arg_changes else ''}{arg_changes}"


# region meh
class HumanAgent(BaseAgent):
    long_name: str = "Human Agent"
    
    def act(self, game_state: GameState, reward, done):
        return input()


class RandomAvailableAgent(BaseAgent):
    long_name: str = "Random Available Agent"
    
    required_info = {
        "admissible_commands": True,
    }
    
    def act(self, game_state: GameState, reward, done):
        return str(random.choice(game_state.admissible_commands))


class PolicyAgent(BaseAgent):
    long_name: str = "Policy Agent"
    
    required_info = {
        "admissible_commands": True,
        "policy_commands": True
    }
    
    def act(self, game_state: GameState, reward, done):
        print(f"{game_state.next_action =}")
        if game_state.next_action:
            return game_state.next_action
        return str(random.choice(game_state.admissible_commands))


# maybe better described as a Preference (and if cant do what it wants then sometimes follows policy) Agent
class PreferenceAgent(BaseAgent):
    long_name: str = "Preference Agent"
    
    required_info = {
        "admissible_commands": True,
        "policy_commands": True
    }
    
    def act(self, game_state: GameState, reward, done):
        # first we figure out if we want to move around.
        # todo: this value may change how it works in the future
        if self.move_chance >= random.random():
            return str(random.choice(game_state.commands_by_type["move"]))
        
        # a preference agent will randomly select an action with the distribution of its preferred_actions.
        # if it cant do that it has a random chance to either do the best command, or do a random command.
        action_type = random.choices(list(self.preferred_actions.keys()), weights=list(self.preferred_actions.values()))[0]
        
        if len(game_state.commands_by_type[action_type]) > 0:
            return str(random.choice(game_state.commands_by_type[action_type]))
        
        return self.act_goal_or_move(game_state)
        
    def act_goal_or_move(self, game_state: GameState):
        follow_best = random.random() > 0.5
        if follow_best and game_state.next_action:
            return self.act_goal(game_state)
        else:
            return self.act_wander(game_state)
# endregion


# region the good ones
# this agent chooses either to move, or to act.
class MovePrefAgent(BaseAgent):
    long_name: str = "Exploration Focused Agent"
    
    def act(self, game_state: GameState, reward, done):
        # choose whether to move or to act
        move_choice = random.random()
        if move_choice <= self.move_chance:
            return self.act_wander(game_state)
        
        # if we have not moved, look at what is currently available, and break the tie with preference
        # get all the actions that we can do
        available_commands_by_type = {action_type: commands for action_type, commands in game_state.commands_by_type.items() if len(commands) > 0 and action_type != "move"}
        # get the preferences that are valid for the actions that we can do
        available_preferences = {action_type: pref for action_type, pref in self.preferred_actions.items() if action_type in available_commands_by_type}
        # get action type from the preferences
        # check if there are any available preferences, because if there are none (like what may happen in the do nothing manager) we need to do something
        if len(available_preferences) > 0:
            preferred_action_type = self.get_preferred_action_type(available_preferences)
            # select an action from that
            action = str(random.choice(available_commands_by_type[preferred_action_type]))
        
            return action

        # default to wandering
        return self.act_wander(game_state)
    
    def get_preferred_action_type(self, available_preferences):
        return random_argmax_from_dict(available_preferences)
    pass


class MovePrefAgent2(MovePrefAgent):
    long_name: str = "Exploration Focused Agent"
    
    def get_preferred_action_type(self, available_preferences):
        return random.choices(list(available_preferences.keys()), weights=list(available_preferences.values()))[0]
    

# This agent looks at objects that they interacted with before and weights them based on how recently they interacted with them (preferring less interacted with objects)
class SaliencyAgent(PreferenceAgent):
    long_name: str = "Novelty Focused Agent"
    
    def __init__(self):
        super().__init__()
        # the max amount of turns that the agent looks back at when figuring out if its interested
        # useful because after some point a thing may have potentially changed enough that it is considered "new"
        self.saliency_turn_max = 50
    
    def act(self, game_state: GameState, reward, done):
        # profile the history
        subject_saliency = self.profile_history()
        
        # combine agent preference with saliency model for each object
        
        # find which action_type has the minimum saliency, inverted and potentially scaled?
        # this represents how much the player would want to interact with the least interacted with object in this room
        action_type_saliency = {
            action_type: 1 / (min([subject_saliency[action.sub] for action in actions]) + 1 if len(actions) else math.inf)
            for action_type, actions in game_state.commands_by_type.items()
            if action_type != "move"
        }
        total_saliency_score = sum(action_type_saliency.values()) if sum(action_type_saliency.values()) > 0 else 1
        action_type_saliency = {
            action_type: saliency / total_saliency_score
            for action_type, saliency in action_type_saliency.items()
        }
        
        # find which action the agent wants to do
        saliency_preferred_actions = {action_type: (preference + action_type_saliency[action_type])/2 for action_type, preference in self.preferred_actions.items()}
        action_type = random.choices(list(saliency_preferred_actions.keys()), weights=list(saliency_preferred_actions.values()))[0]
        
        # if that action exists then pick the minimum saliency object for that action type
        if len(game_state.commands_by_type[action_type]) > 0:
            action_saliency = {action: subject_saliency[action.sub] for action in game_state.commands_by_type[action_type]}
            return str(min(action_saliency, key=action_saliency.get))
        
        # if it doesnt, either follow the best course of action to progress the story (which is often a move) or make a move to a different area.
        return self.act_goal_or_move(game_state)
    
    def profile_history(self):
        subject_recency = defaultdict(list)
        for i, (action, infos) in enumerate(reversed(self.action_history)):
            # we dont care about things that are too long ago
            if i > self.saliency_turn_max:
                break
            
            subject = infos["action"].get("subject", "")
            verb = infos["action"].get("verb", "")
            if subject == "" or verb == "":
                continue
            
            # keyword: eligibility traces?
            # the longer it was ago the less uninteresting it is
            recency_metric = self.saliency_curve(i)
            subject_recency[subject].append(recency_metric)
        
        # the saliency of a subject is based on how long ago it was, with 0 being the most salient
        subject_saliency = {subject: sum(recency_list) for subject, recency_list in subject_recency.items()}
        subject_saliency = defaultdict(int, subject_saliency)
        return subject_saliency
    
    def saliency_curve(self, i):
        recency_metric = 1 / (i + 1)
        return recency_metric


class SimplePreferenceAgent(PreferenceAgent):
    long_name: str = "Goal Focused Agent"

    def act(self, game_state: GameState, reward, done):
        # randomly select an action type
        action_type = random.choices(list(self.preferred_actions.keys()), weights=list(self.preferred_actions.values()))[0]
    
        # if it exists try to do one of those
        if len(game_state.commands_by_type[action_type]) > 0:
            return str(random.choice(game_state.commands_by_type[action_type]))
    
        # otherwise just move around
        # return str(random.choice(game_state.commands_by_type["move"]))
        return self.act_goal_or_move(game_state)
# endregion


# region meh
class FlatSaliencyAgent(SaliencyAgent):
    long_name: str = "Flat Saliency Agent"
    
    def saliency_curve(self, i):
        recency_metric = (-i / self.saliency_turn_max) + 1
        return recency_metric
    
    
class SimpleSaliencyAgent(SaliencyAgent):
    long_name: str = "Simple Saliency Agent"
    
    def act(self, game_state: GameState, reward, done):
        subject_saliency = self.profile_history()
        
        # find which action the agent wants to do
        action_type = random.choices(list(self.preferred_actions.keys()), weights=list(self.preferred_actions.values()))[0]
        
        # if that action exists then pick the minimum saliency object for that action type
        if len(game_state.commands_by_type[action_type]) > 0:
            action_saliency = {action: subject_saliency[action.sub] for action in game_state.commands_by_type[action_type]}
            return str(random_argmin_from_dict(action_saliency))
        
        # if it doesnt, either follow the best course of action to progress the story (which is often a move) or make a move to a different area.
        return self.act_goal_or_move(game_state)
    pass


# this agent chooses either to move, or to act.
class MovePrefSaliencyAgent(SaliencyAgent):
    long_name: str = "Move Pref. Saliency Agent"
    
    def act(self, game_state: GameState, reward, done):
        # choose whether to move or to act
        move_choice = random.random()
        
        if move_choice <= self.move_chance:
            return str(random.choice(game_state.commands_by_type["move"]))
        
        # if we have not moved, look at what is currently available, and break the tie with preference
        # get all the actions that we can do
        available_commands_by_type = {action_type: commands for action_type, commands in game_state.commands_by_type.items() if len(commands) > 0 and action_type != "move"}
        # get the preferences that are valid for the actions that we can do
        available_preferences = {action_type: pref for action_type, pref in self.preferred_actions.items() if action_type in available_commands_by_type}
        # get action type from the preferences
        # check if there are any available preferences, because if there are none (like what may happen in the do nothing manager) we need to do something
        if len(available_preferences) == 0:
            return str(random.choice(game_state.commands_by_type["move"]))
        
        # todo: calculate saliency and use that to choose an object to interact with
        
        preferred_action_type = random_argmax_from_dict(available_preferences)
        
        # select an action from that, using saliency to pick the subject
        subject_saliency = self.profile_history()
        
        # find match ups between the saliency and the subjects of preferred commands
        preferred_commands = available_commands_by_type[preferred_action_type]
        scored_commands = {command: subject_saliency[command.sub] for command in preferred_commands}
        
        # pick the most salient (aka lowest score)
        action = str(random_argmin_from_dict(scored_commands))
        
        return action
    pass
# endregion
    

if __name__ == '__main__':
    pass
