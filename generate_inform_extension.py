import json
import os.path
import string
from json import JSONEncoder, JSONDecoder

from graph_data import ensure_dir

description_letters = string.ascii_letters


# this class is mostly for the ability to access fields with the dot operator.
# todo: allow for defining of multiple action patterns as some distractions have more than one way to interact
class Distraction:
    def __init__(
            self,
            num_distractions=0,
            t_type=None,
            d_type=None,
            table_name=None,
            table_name_pattern=None,
            table_desc_pattern=None,
            action_pattern=None,
            t_action=None,
            d_action=None,
            t_action_text=None,
            d_action_text=None,
            dm_action_label=None,
    ):
        # for automatically building the table
        self.num_distractions = num_distractions
        
        # ---field definitions---
        # type is the type of the distractions and non distractions that may already exist in the world
        self.t_type = t_type
        
        # d_type is the type for only the distractions
        self.d_type = d_type
        
        # table holds all of the actual distraction objects
        self.table_name = table_name
        self.table = []
        self.table_name_pattern = table_name_pattern
        self.table_desc_pattern = table_desc_pattern
        
        # action pattern is the pattern used by the python side of things.
        # it should match the pattern given by t and d action text, using {sub} for the subject
        self.action_pattern = action_pattern
        
        # action governs the label of the action associated with the type,
        # they should look similar but have to be different to differentiate between regular interaction and distraction
        self.t_action = t_action
        self.d_action = d_action
        
        # action text is the text that is typed to interact with an object of that type.
        # the action_pattern can be used for simplicity most of the time
        self.t_action_text = t_action_text
        self.d_action_text = d_action_text
        
        # action label is for the python side label of the action and is label by which we decide what distraction to decide on
        self.dm_action_label = dm_action_label
        
        self.build_table_numbered()
    
    def build_table_numbered(self):
        for d_char in description_letters[:self.num_distractions]:
            self.table.append({
                "name": self.table_name_pattern.format(**vars(self), d_char=d_char),
                "desc": self.table_desc_pattern.format(**vars(self), d_char=d_char),
            })
    
    def save_state(self):
        return vars(self)
    
    def load_state(self, fields_dict):
        for key, value in fields_dict.items():
            self.__dict__[key] = value
        return self


class DistractionNumbered(Distraction):
    def __init__(self, d_num, num_distractions):
        t_type = f"distract_{d_num}_thing"
        d_type = f"distract_{d_num}_distraction"
        action_pattern = f"distract {d_num} {{sub}}"
        
        super().__init__(
            num_distractions=num_distractions,
            t_type=t_type,
            d_type=d_type,
            table_name=f"Table of distract_{d_num} Distractors",
            table_name_pattern=f"{{d_char}}_distract_{d_num}",
            table_desc_pattern=f"{{d_char}} distract_{d_num}",
            action_pattern=action_pattern,
            t_action=f"interact_distract_{d_num}_thing",
            d_action=f"interact_distract_{d_num}_distraction",
            t_action_text=action_pattern.format(sub=f"[{t_type}]"),
            d_action_text=action_pattern.format(sub=f"[{d_type}]"),
            dm_action_label=f"distract_{d_num}",
        )
    pass


class DistractionNamed(Distraction):
    def __init__(self, name, action_pattern, action_label, num_distractions):
        t_type = f"{name}_thing"
        d_type = f"{name}_distraction"
        
        super().__init__(
            num_distractions=num_distractions,
            t_type=t_type,
            d_type=d_type,
            table_name=f"Table of {name} Distractors",
            table_name_pattern=f"{{d_char}}_{name}",
            table_desc_pattern=f"{{d_char}} {name}",
            action_pattern=action_pattern,
            t_action=f"interact_distract_{name}_thing",
            d_action=f"interact_distract_{name}_distraction",
            t_action_text=action_pattern.format(sub=f"[{t_type}]"),
            d_action_text=action_pattern.format(sub=f"[{d_type}]"),
            dm_action_label=action_label,
        )


# JSON encoder and decoder to more gracefully store and read from file.
class DistractionEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Distraction):
            obj_dict = obj.save_state()
            obj_dict["class"] = type(obj).__name__
            obj_dict["base_class"] = Distraction.__name__
            return obj_dict
        return super().default(obj)
    
    pass


class DistractionsDecoder(JSONDecoder):
    def decode(self, s, **kwargs):
        obj = super().decode(s, **kwargs)
        # assume list
        if type(obj) == list:
            for i, distraction in enumerate(obj):
                # check to see if its correct class
                if distraction["base_class"] != Distraction.__name__:
                    continue
                # replace it with a distraction object if it is the correct type
                obj[i] = Distraction().load_state(distraction)
        return obj


def generate_distraction_objects_numbered(num_distraction_types=50, num_distractions=20):
    distractions = []
    for d_num in range(num_distraction_types):
        distraction = DistractionNumbered(d_num, num_distractions)
        distractions.append(distraction)
    
    return distractions


def generate_distraction_objects_named(distraction_type_names, num_distractions=20):
    distractions = []
    for d_name in distraction_type_names:
        distraction = DistractionNumbered(d_name, num_distractions)
        distractions.append(distraction)
    
    return distractions


def generate_distraction_base(num_distractions=20):
    # generated look, talk, touch distractions
    # these have some amount of custom handling in CatWorldEnv, but distraction wise must be defined here
    look = DistractionNamed("look", "look at {sub}", "look", num_distractions)
    talk = DistractionNamed("talk", "talk to {sub}", "talk", num_distractions)
    touch = DistractionNamed("touch", "touch {sub}", "touch", num_distractions)
    return [look, talk, touch]


def generate_distraction_definition_text(distractions):
    # load the template
    with open("distraction_gen/distraction_gen_templates/distraction_type_template.txt", "r") as fp:
        template = fp.read()
    
    # store each distraction's i7 definition into a list
    distraction_sections = []
    
    # fill in the template
    for distraction in distractions:
        # build table entries
        table_list = []
        for entry in distraction.table:
            table_list.append('{name}	1	"{desc}"'.format(**entry))
        table_entries = "\n".join(table_list)
        
        # fill in the template
        text = template.format(**vars(distraction), table_entries=table_entries)
        distraction_sections.append(text)
    
    # turn into text and return
    return "\n\n".join(distraction_sections)


def generate_distraction_decision_text(distractions):
    # load the templates
    with open("distraction_gen/distraction_gen_templates/distraction_decision_template.txt", "r") as fp:
        decision_template = fp.read()
    with open("distraction_gen/distraction_gen_templates/distraction_decision_entry_template.txt", "r") as fp:
        entry_template = fp.read()
    
    # compile the decision entries
    decision_list = []
    for i, distraction in enumerate(distractions):
        otherwise_clause = "" if i == 0 else "otherwise "
        decision_list.append(entry_template.format(**vars(distraction), otherwise_clause=otherwise_clause))
    
    # combine together into the whole thing
    decision_entries = "\n".join(decision_list)
    return decision_template.format(decision_entries=decision_entries)


def generate_dm_actions_text(distractions):
    # load the templates
    with open("distraction_gen/distraction_gen_templates/distractions_dm_actions_template.txt") as fp:
        actions_template = fp.read()
    
    # build the lists
    all_distractions_list = []
    for distraction in distractions:
        all_distractions_list.append(f'"{distraction.dm_action_label}"')
        
    # turn the lists into text
    all_distractions_list_text = f"{{{', '.join(all_distractions_list)}}}"
    
    # fill the template with the text
    return actions_template.format(all_distractions_list_text=all_distractions_list_text)


def generate_print_info_text(distractions):
    # load the templates
    with open("distraction_gen/distraction_gen_templates/distraction_print_info_template.txt") as fp:
        print_info_template = fp.read()
    with open("distraction_gen/distraction_gen_templates/distraction_add_info_template.txt", "r") as fp:
        add_info_template = fp.read()
    
    # build the lists
    add_info_list = []
    for distraction in distractions:
        add_info_list.append(add_info_template.format(**vars(distraction)))
    
    # turn the lists into text
    add_info_text = "\n".join(add_info_list)
    
    # fill the template with the text
    return print_info_template.format(add_info_text=add_info_text)


def build_extension(distractions, file_name=None):
    # create text from the distractions
    distraction_definitions = generate_distraction_definition_text(distractions)
    distraction_decisions = generate_distraction_decision_text(distractions)
    distraction_dm_actions = generate_dm_actions_text(distractions)
    distraction_print_info = generate_print_info_text(distractions)
    
    # default filename
    if file_name is None:
        file_name = "Inform7 projects/text world doubt.materials/Extensions/Anton Vinogradov/Distractions.i7x"
    
    # load the extension template
    with open("distraction_gen/distraction_gen_templates/distraction_extension_template.txt", "r") as fp:
        template = fp.read()
    
    # create the template filler
    template_filler = {
        "distraction_definitions": distraction_definitions,
        "distraction_decisions": distraction_decisions,
        "distraction_dm_actions": distraction_dm_actions,
        "distraction_print_info": distraction_print_info
    }
    
    ensure_dir(file_name)
    
    # fill the template
    file_text = template.format(**template_filler)
    
    # ensure we are using TABS and not SPACES like my editor so very much loves to do
    file_text = file_text.replace("    ", "\t")
    
    # save to file
    with open(file_name, "w") as fp:
        fp.write(file_text)
    pass


def main():
    num_distraction_types = 10
    num_distractions = 20
    
    # create the distractions
    # todo: add some of these objects to the world
    standard_distractions = generate_distraction_base(num_distractions)
    extra_distractions = generate_distraction_objects_named(["book_read", "food_eat"], num_distractions)
    # extra_distractions = generate_distraction_objects_numbered(num_distraction_types, num_distractions)
    
    # create the text for the extension, and then save it. Both the named and generic distractions
    build_extension(extra_distractions + standard_distractions)
    
    # dump what distractions we created to file so the main program can use it.
    # only the generic distractions, the others have their custom handlers already in CatWorldEnv
    with open("distraction_gen/distraction_gen_info/distraction.json", "w") as fp:
        json.dump(extra_distractions, fp, cls=DistractionEncoder)
    
    pass


if __name__ == '__main__':
    main()
