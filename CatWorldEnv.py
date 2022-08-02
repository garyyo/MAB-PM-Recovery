"""
Author: Anton Vinogradov
This file handles environment processing. It stands as a replacement for the built in textworld env object,
but is in no way actually compatible.
"""

import random
import json
from json import JSONEncoder
from collections import defaultdict

try:
    import textworld
except ModuleNotFoundError:
    print("you are trying to do something with textworld, you need to be in a linux environment and install textworld, bypassing for now, but know that stuff will likely break")
    
    # This is a weird thing where the class pretends to be an imported thing just enough to fool the parts of my code that rely on it.
    # Really need to find a better way to do this as this is only for testing stuff in Windows environments, which is slightly faster than WSL
    class textworld:
        @staticmethod
        def EnvInfos():
            return None

# define the Global action and command info stuff
type_to_action, action_to_type, admissible_commands_info = {}, {}, {}


def random_argmin_from_dict(d):
    min_val = min(d.values())
    return random.choice([k for k, v in d.items() if v == min_val])


def random_argmax_from_dict(d):
    max_val = max(d.values())
    return random.choice([k for k, v in d.items() if v == max_val])


class GameState(dict):
    default_values = defaultdict(lambda: None, {
        "facts": [],
        "entities": [],
        "variables": defaultdict(bool),
        "admissible_commands": [],
        "commands": defaultdict(list),
        "next_action": "",
        "policy_commands": [],
        "command_templates": [],
        "score": 0,
        "feedback": "",
        "location": "",
        "completed": False,
        "inventory": [],
        "action": defaultdict(str),
    })

    def __init__(self, infos, requested_infos=textworld.EnvInfos()):
        super().__init__(infos)
        self.requested = requested_infos
        self.admissible_commands = None

        # extracting a bunch of the values we want exposed as attributes,
        # only if they are not false (aka true or missing) in the requested infos,
        # otherwise use a default value to keep interoperability, but dont copy it from infos
        for field, default in self.default_values.items():
            setattr(self, field, infos[field] if getattr(requested_infos, field, True) and field in infos else default)

        # adding a couple things
        self.variables = defaultdict(bool, infos.get("variables", {}) if requested_infos.facts else defaultdict(bool))
        self.commands_by_type = infos.get("commands", defaultdict(list)) if requested_infos.admissible_commands else []
        self.next_action = infos.get("next_action", "") if requested_infos.policy_commands else ""
        self.completed = self.variables.get("completed", False)

        self.dm_model = None

    def set_dm_model(self, model):
        self.dm_model = model
        
        
class GameCommand:
    def __init__(self, sub, obj, verb_type, verb_pattern):
        self.sub = sub
        self.obj = obj
        self.verb_type = verb_type
        self.verb_pattern = verb_pattern
        
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        return self.verb_pattern.format(sub=self.sub, obj=self.obj)
    
    
class GameStateJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GameCommand):
            return str(obj)
        return super().default(obj)
    pass


def env_compat_layer(obs, old_infos=None, requested_infos=None):
    if old_infos is None:
        old_infos = {}

    new_obs = []
    json_string = ""
    info_state = False
    for line in obs.split("\n"):
        # the lines between INFO and END INFO
        if line == "INFO":
            info_state = True
            continue
        if line == "END INFO":
            info_state = False
            continue
        if info_state:
            json_string += f"{line}\n"
        else:
            new_obs.append(line)

    new_infos = json.loads(json_string)

    # if the game asks for a clarification, we need to preserve the infos. hopefully this never actually happens
    if len(new_infos) == 0:
        return new_obs, old_infos, old_infos, False

    new_obs = "\n".join(new_obs)

    talk_commands, pickup_commands, use_commands, move_commands, look_commands, generic_distraction_actions = get_admissible_commands(new_infos)
    flat_generic_distraction_actions = [distraction_action for specific_distraction_actions in generic_distraction_actions.values() for distraction_action in specific_distraction_actions]
    all_commands = talk_commands + pickup_commands + use_commands + move_commands + look_commands + flat_generic_distraction_actions

    new_infos["admissible_commands"] = all_commands
    new_infos["commands"] = {
        "talk": talk_commands,
        "touch": pickup_commands + use_commands,
        "look": look_commands,
        "move": move_commands,
        **generic_distraction_actions,
    }

    game_state = GameState(new_infos, requested_infos)

    return new_obs, game_state, old_infos, game_state.completed


def get_admissible_commands(infos):
    # commands that dont really belong in a category cuz i dont want them to be counted
    extra_commands = []

    # talking, built from the list of talking
    talk_commands = []
    for person, dialogues in infos["possible_talk"].items():
        if len(dialogues) == 0:
            talk_commands.append(GameCommand(person, "", "talk", "talk to {sub}"))
        for dialogue in dialogues:
            talk_commands.append(GameCommand(person, dialogue, "talk", "talk to {sub} about {obj}"))

    # looking, built from the list of looking
    look_commands = []
    for book in infos["signs"]:
        look_commands.append(GameCommand(book, "", "look", "look at {sub}"))

    # picking up items
    pickup_commands = []
    for item in infos["items"]:
        if item not in infos["inventory"]:
            pickup_commands.append(GameCommand(item, "", "touch", "pick up {sub}"))
            extra_commands.append(GameCommand(item, "", "look", "examine {sub}"))

    # using anything you picked up on everything else.
    use_commands = []
    for item in infos["inventory"]:
        for person in infos["people"]:
            use_commands.append(GameCommand(person, item, "touch", "give {sub} {obj}"))
        for door in infos["locked_exits"]:
            use_commands.append(GameCommand(door, item, "touch", "unlock {sub} with {obj}"))
            
    # moving to a new location
    move_commands = []
    for direction in infos["viable_directions"]:
        move_commands.append(GameCommand(direction, "item", "move", "go {sub}"))
        
    # dealing with specific distractions
    for item in infos["look_thing"]:
        look_commands.append(GameCommand(item, "", "look", "look at {sub}"))
    for item in infos["talk_thing"]:
        talk_commands.append(GameCommand(item, "", "talk", "talk to {sub}"))
    for item in infos["touch_thing"]:
        use_commands.append(GameCommand(item, "", "touch", "touch {sub}"))

    # dealing with generic distractions
    generic_distraction_actions = {}
    for key, values in admissible_commands_info.items():
        action = values["dm_action_label"]
        pattern = values["action_pattern"]
        generic_distraction_actions[action] = []
        for distract in infos[key]:
            generic_distraction_actions[action].append(GameCommand(distract, "", action, pattern))

    return talk_commands, pickup_commands, use_commands, move_commands, look_commands, generic_distraction_actions


# this function must be called at least once when the game starts up.
def load_distractions(distractions):
    global type_to_action, action_to_type, admissible_commands_info
    type_to_action = {
        "look": ["looking at", "interact_distract_look_distraction", "examining"],
        "talk": ["talking to", "list topics", "interact_distract_talk_distraction"],
        "touch": ["taking", "giving it to", "unlocking it with", "opening", "interact_distract_touch_distraction"],
        "move": ["go", ""],
        **{distraction.dm_action_label: [distraction.t_action, distraction.d_action] for distraction in distractions},
    }
    action_to_type = {action: action_type for action_type, actions in type_to_action.items() for action in actions}

    admissible_commands_info = {
        distraction.t_type: {
            "dm_action_label": distraction.dm_action_label,
            "action_pattern": distraction.action_pattern,
        }
        for distraction in distractions
    }
    

if __name__ == '__main__':
    pass
