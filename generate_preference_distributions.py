import os
import random
import json
import CatWorldEnv

# what sort of actions are preferred in the history
history_preferred_actions = ["touch"]
saturated_actions = ["look", "talk", "touch"]


def gen_mode(test_mode):
    # the mode defines how many action types are consider "preferred"
    action_types = list(CatWorldEnv.type_to_action.keys())
    action_types.remove("move")
    
    # back history is defined by history_preferred_actions
    if test_mode == "history":
        num_preferred_actions = len(history_preferred_actions)
        preferred_actions = history_preferred_actions
    else:
        num_preferred_actions = test_mode + 1
        # we want to error if we are trying to select more action types to prefer than there are available
        assert num_preferred_actions <= len(action_types)
        # read cant be preferred because it is preferred when generating history and we want it to be different.
        valid_preferences = list(set(action_types) - set(history_preferred_actions))
        
        preferred_actions = random.sample(valid_preferences, k=num_preferred_actions)
        # if all of the preferred actions are in the "environmentally saturated" category, then we replace one with an unsaturated one
        if len(set(preferred_actions) - set(saturated_actions)) == 0:
            # only replace if there are actions left to replace with, never should crop up
            possible_actions_left = list(set(action_types) - set(saturated_actions) - set(preferred_actions))
            if len(possible_actions_left) > 0:
                unsaturated_action_type = random.choice(possible_actions_left)
                preferred_actions[0] = unsaturated_action_type
            else:
                print("only environmentally saturated action types are available, cannot replace with unsaturated action type")
        pass
    
    # 75% of the actions must be dedicated to the preferred actions.
    # of those preferred actions, the preference is split equally
    preferred_weight = 75 / num_preferred_actions
    baseline_weight = 25 / (len(action_types) - num_preferred_actions)
    
    # assign the correct weights
    preference_dist = {
        action_type: preferred_weight if action_type in preferred_actions else baseline_weight
        for action_type in action_types
    }
    
    # save for later
    save_path = save_mode(test_mode, preference_dist)
    
    return preference_dist, save_path


def gen_mode_static(test_mode):
    if test_mode == "history":
        preference_dist = {
            "look": 1.0,
            "talk": 1.0,
            "touch": 11.0,
            "distract_book_read": 1.0,
            "distract_food_eat": 1.0,
        }
    else:
        preference_dist = [
            {
                "look": 1.0,
                "talk": 1.0,
                "touch": 1.0,
                "distract_book_read": 16.0,
                "distract_food_eat": 1.0,
            },
            {
                "look": 1.0,
                "talk": 1.0,
                "touch": 1.0,
                "distract_book_read": 8.5,
                "distract_food_eat": 8.5,
            },
            {
                "look": 1.0,
                "talk": 6.0,
                "touch": 1.0,
                "distract_book_read": 6.0,
                "distract_food_eat": 6.0,
            }
        ][test_mode]
    
    # save for later
    save_path = save_mode(test_mode, preference_dist)
    
    return preference_dist, save_path


def all_modes_iterator(skip=None):
    action_types = [action_type for action_type in CatWorldEnv.type_to_action.keys() if action_type != "move"]
    for action_type in action_types:
        if action_type == skip:
            continue
        preference_dist = {a: 1 if a != action_type else 11 for a in action_types}
        name = f"{action_type}"
        yield preference_dist, name, action_type
    pass


def save_mode(test_mode, preference_dist):
    save_path = f"backhistory/{test_mode}/preference_dist.json"
    save_dir = os.path.dirname(save_path)
    
    # ensure that the directory exists
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    with open(save_path, "w") as fp:
        json.dump(preference_dist, fp)
    return save_path


def load_mode(test_mode):
    with open(f"backhistory/{test_mode}/preference_dist.json", "r") as fp:
        return json.load(fp)


def load_mode_file(pref_file):
    with open(pref_file, "r") as fp:
        return json.load(fp)


# what the old preferences looked like. they were statically defined rather than generated.
# preference_back_history = {
#     "read": 1.0,
#     "talk": 1.0,
#     "touch": 11.0,
#     "distract_1": 1.0,
#     "distract_2": 1.0,
# }
# preference_modal = [
#     {
#         "read": 11.0,
#         "talk": 1.0,
#         "touch": 1.0,
#         "distract_1": 1.0,
#         "distract_2": 1.0,
#     },
#     {
#         "read": 6.0,
#         "talk": 1.0,
#         "touch": 1.0,
#         "distract_1": 6.0,
#         "distract_2": 1.0,
#     },
#     {
#         "read": 5.0,
#         "talk": 4.0,
#         "touch": 1.0,
#         "distract_1": 1.0,
#         "distract_2": 4.0,
#     }
# ]


if __name__ == '__main__':
    print(list(all_modes_iterator()))
    pass
