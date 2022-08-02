Distractions by Anton Vinogradov begins here.

Volume Distractions

A thing can be distracting. A thing is usually not distracting.
A thing is either used or unused. A thing is usually unused.
A thing is either d_tracked or d_untracked. A thing is usually d_untracked.

Book Distraction Definitions

Section distract_book_read

[defining types]
A distract_book_read_thing is a kind of thing.
A distract_book_read_distraction is a kind of distract_book_read_thing. distract_book_read_distraction is distracting.

[defining the actual objects]
distract_book_read_distraction are defined by the Table of distract_book_read Distractors

[defining what the interactions are possible]
interact_distract_book_read_thing is an action applying to one visible thing.
understand "distract book_read [distract_book_read_thing]" as interact_distract_book_read_thing.
interact_distract_book_read_distraction is an action applying to one visible thing.
understand "distract book_read [distract_book_read_distraction]" as interact_distract_book_read_distraction.

[the basics of interaction]
before of interact_distract_book_read_distraction a distract_book_read_distraction:
	say "distracting with [description of noun].";

after interact_distract_book_read_distraction:
	set "distracted";
	reset distracted in one turn from now;

[table]
Table of distract_book_read Distractors
name	chance	description
a_distract_book_read	1	"a distract_book_read"
b_distract_book_read	1	"b distract_book_read"
c_distract_book_read	1	"c distract_book_read"
d_distract_book_read	1	"d distract_book_read"
e_distract_book_read	1	"e distract_book_read"
f_distract_book_read	1	"f distract_book_read"
g_distract_book_read	1	"g distract_book_read"
h_distract_book_read	1	"h distract_book_read"
i_distract_book_read	1	"i distract_book_read"
j_distract_book_read	1	"j distract_book_read"
k_distract_book_read	1	"k distract_book_read"
l_distract_book_read	1	"l distract_book_read"
m_distract_book_read	1	"m distract_book_read"
n_distract_book_read	1	"n distract_book_read"
o_distract_book_read	1	"o distract_book_read"
p_distract_book_read	1	"p distract_book_read"
q_distract_book_read	1	"q distract_book_read"
r_distract_book_read	1	"r distract_book_read"
s_distract_book_read	1	"s distract_book_read"
t_distract_book_read	1	"t distract_book_read"

Section distract_food_eat

[defining types]
A distract_food_eat_thing is a kind of thing.
A distract_food_eat_distraction is a kind of distract_food_eat_thing. distract_food_eat_distraction is distracting.

[defining the actual objects]
distract_food_eat_distraction are defined by the Table of distract_food_eat Distractors

[defining what the interactions are possible]
interact_distract_food_eat_thing is an action applying to one visible thing.
understand "distract food_eat [distract_food_eat_thing]" as interact_distract_food_eat_thing.
interact_distract_food_eat_distraction is an action applying to one visible thing.
understand "distract food_eat [distract_food_eat_distraction]" as interact_distract_food_eat_distraction.

[the basics of interaction]
before of interact_distract_food_eat_distraction a distract_food_eat_distraction:
	say "distracting with [description of noun].";

after interact_distract_food_eat_distraction:
	set "distracted";
	reset distracted in one turn from now;

[table]
Table of distract_food_eat Distractors
name	chance	description
a_distract_food_eat	1	"a distract_food_eat"
b_distract_food_eat	1	"b distract_food_eat"
c_distract_food_eat	1	"c distract_food_eat"
d_distract_food_eat	1	"d distract_food_eat"
e_distract_food_eat	1	"e distract_food_eat"
f_distract_food_eat	1	"f distract_food_eat"
g_distract_food_eat	1	"g distract_food_eat"
h_distract_food_eat	1	"h distract_food_eat"
i_distract_food_eat	1	"i distract_food_eat"
j_distract_food_eat	1	"j distract_food_eat"
k_distract_food_eat	1	"k distract_food_eat"
l_distract_food_eat	1	"l distract_food_eat"
m_distract_food_eat	1	"m distract_food_eat"
n_distract_food_eat	1	"n distract_food_eat"
o_distract_food_eat	1	"o distract_food_eat"
p_distract_food_eat	1	"p distract_food_eat"
q_distract_food_eat	1	"q distract_food_eat"
r_distract_food_eat	1	"r distract_food_eat"
s_distract_food_eat	1	"s distract_food_eat"
t_distract_food_eat	1	"t distract_food_eat"

Section look

[defining types]
A look_thing is a kind of thing.
A look_distraction is a kind of look_thing. look_distraction is distracting.

[defining the actual objects]
look_distraction are defined by the Table of look Distractors

[defining what the interactions are possible]
interact_distract_look_thing is an action applying to one visible thing.
understand "look at [look_thing]" as interact_distract_look_thing.
interact_distract_look_distraction is an action applying to one visible thing.
understand "look at [look_distraction]" as interact_distract_look_distraction.

[the basics of interaction]
before of interact_distract_look_distraction a look_distraction:
	say "distracting with [description of noun].";

after interact_distract_look_distraction:
	set "distracted";
	reset distracted in one turn from now;

[table]
Table of look Distractors
name	chance	description
a_look	1	"a look"
b_look	1	"b look"
c_look	1	"c look"
d_look	1	"d look"
e_look	1	"e look"
f_look	1	"f look"
g_look	1	"g look"
h_look	1	"h look"
i_look	1	"i look"
j_look	1	"j look"
k_look	1	"k look"
l_look	1	"l look"
m_look	1	"m look"
n_look	1	"n look"
o_look	1	"o look"
p_look	1	"p look"
q_look	1	"q look"
r_look	1	"r look"
s_look	1	"s look"
t_look	1	"t look"

Section talk

[defining types]
A talk_thing is a kind of thing.
A talk_distraction is a kind of talk_thing. talk_distraction is distracting.

[defining the actual objects]
talk_distraction are defined by the Table of talk Distractors

[defining what the interactions are possible]
interact_distract_talk_thing is an action applying to one visible thing.
understand "talk to [talk_thing]" as interact_distract_talk_thing.
interact_distract_talk_distraction is an action applying to one visible thing.
understand "talk to [talk_distraction]" as interact_distract_talk_distraction.

[the basics of interaction]
before of interact_distract_talk_distraction a talk_distraction:
	say "distracting with [description of noun].";

after interact_distract_talk_distraction:
	set "distracted";
	reset distracted in one turn from now;

[table]
Table of talk Distractors
name	chance	description
a_talk	1	"a talk"
b_talk	1	"b talk"
c_talk	1	"c talk"
d_talk	1	"d talk"
e_talk	1	"e talk"
f_talk	1	"f talk"
g_talk	1	"g talk"
h_talk	1	"h talk"
i_talk	1	"i talk"
j_talk	1	"j talk"
k_talk	1	"k talk"
l_talk	1	"l talk"
m_talk	1	"m talk"
n_talk	1	"n talk"
o_talk	1	"o talk"
p_talk	1	"p talk"
q_talk	1	"q talk"
r_talk	1	"r talk"
s_talk	1	"s talk"
t_talk	1	"t talk"

Section touch

[defining types]
A touch_thing is a kind of thing.
A touch_distraction is a kind of touch_thing. touch_distraction is distracting.

[defining the actual objects]
touch_distraction are defined by the Table of touch Distractors

[defining what the interactions are possible]
interact_distract_touch_thing is an action applying to one visible thing.
understand "touch [touch_thing]" as interact_distract_touch_thing.
interact_distract_touch_distraction is an action applying to one visible thing.
understand "touch [touch_distraction]" as interact_distract_touch_distraction.

[the basics of interaction]
before of interact_distract_touch_distraction a touch_distraction:
	say "distracting with [description of noun].";

after interact_distract_touch_distraction:
	set "distracted";
	reset distracted in one turn from now;

[table]
Table of touch Distractors
name	chance	description
a_touch	1	"a touch"
b_touch	1	"b touch"
c_touch	1	"c touch"
d_touch	1	"d touch"
e_touch	1	"e touch"
f_touch	1	"f touch"
g_touch	1	"g touch"
h_touch	1	"h touch"
i_touch	1	"i touch"
j_touch	1	"j touch"
k_touch	1	"k touch"
l_touch	1	"l touch"
m_touch	1	"m touch"
n_touch	1	"n touch"
o_touch	1	"o touch"
p_touch	1	"p touch"
q_touch	1	"q touch"
r_touch	1	"r touch"
s_touch	1	"s touch"
t_touch	1	"t touch"

Book Distraction Methods and Timers

At the time when reset distracted:
	unset "distracted";

At the time when distractions clear:
	say "distractions cleared.";
	repeat with d running through distracting things that are d_tracked:
		now d is nowhere;
		now d is unused;
		now d is d_untracked;

To distract me with (d - thing):
	if d is not nothing:
		now d is in location;
		now d is used;
	otherwise:
		say "nothing to distract you with my dear.";

To temp distract me with (d - thing):
	distract me with d;
	now d is d_tracked;

To decide which thing is distraction picked from (l_d - list of things):
	If the number of entries in l_d > 0:
		let r be a random number from 1 to the number of entries in l_d;
		[let r be 1;]
		let d be entry r in l_d;
		decide on d;
	decide on nothing;

To decide which list of things is distraction list of (d_type - text):
	let d_list be the list of distracting things that are unused;
	if d_type is "distract_book_read":
		now d_list is the list of distract_book_read_distraction that are unused;
	otherwise if d_type is "distract_food_eat":
		now d_list is the list of distract_food_eat_distraction that are unused;
	otherwise if d_type is "look":
		now d_list is the list of look_distraction that are unused;
	otherwise if d_type is "talk":
		now d_list is the list of talk_distraction that are unused;
	otherwise if d_type is "touch":
		now d_list is the list of touch_distraction that are unused;
	decide on d_list;

Book DM actions

spawn distraction is an action applying to one topic.
understand "DM spawn distraction [text]" as spawn distraction.

spawn distraction temp is an action applying to one topic.
understand "DM spawn distraction temp [text]" as spawn distraction temp.

clear some distractions is an action applying to one topic.
Understand "DM clear distractions [text]" as clear some distractions.

possible_distractions is a list of texts that varies.
possible_distractions is {"distract_book_read", "distract_food_eat", "look", "talk", "touch"}.

after spawn distraction:
	if "[the topic understood]" is "each":
		repeat with p running through possible_distractions:
			distract me with the distraction picked from distraction list of p;
	otherwise:
		repeat with p running through possible_distractions:
			if the topic understood matches the text p:
				distract me with the distraction picked from distraction list of p;

after spawn distraction temp:
	if "[the topic understood]" is "each":
		repeat with p running through possible_distractions:
			temp distract me with the distraction picked from distraction list of p;
	otherwise:
		repeat with p running through possible_distractions:
			if the topic understood matches the text p:
				temp distract me with the distraction picked from distraction list of p;
	distractions clear in 1 turns from now;

after clear some distractions:
	say "I am trying to clear these distractions but I just havent implemented them yet.";

Book Distraction Print Info

To decide which text is printActionables:
	let infos be a list of text;
	add addInfoObjects "distractions" - list of distracting things that are visible to infos;
	add addInfoObjects "distract_book_read_thing" - list of visible distract_book_read_thing to infos;
	add addInfoObjects "distract_food_eat_thing" - list of visible distract_food_eat_thing to infos;
	add addInfoObjects "look_thing" - list of visible look_thing to infos;
	add addInfoObjects "talk_thing" - list of visible talk_thing to infos;
	add addInfoObjects "touch_thing" - list of visible touch_thing to infos;
	decide on formatIterableNewlines infos;



Distractions ends here.