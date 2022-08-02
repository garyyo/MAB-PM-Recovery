"testworld" by anton vinogradov

Include Distractions by Anton Vinogradov

Use serial comma.

[valid headings:
	Volume
	Book
	Part
	Chapter
	Section
]

Volume 1 - Rules of Behavior

[every thing in this volume is dedicated to establishing how the rules work]

Book 1 - Character Speech

[every person you can talk to has a table which handles their dialog.
This dialogue table has pre conditions that must be set before ]
People has a table name called dialogTable. 

[helper to put a label on character speech.]
To say (words - text) as (character - thing):
	say "[character]: [words]"

[The generalized asking characters about things using the internal "asking it about" action]	
Instead of asking a person about a topic listed in the dialogTable of noun:
	if preconditions pre entry:
		reply with noun about topic understood;
	else:
		reply with noun about "default";
		
After asking a person about:
	if there is a topicReadable of "default" in the dialogTable of noun:
		reply with noun about "default";
	else:
		say "They do not seem interested in talking about that.";
		
To reply with (noun - a person) about (topic - text):
	choose row with a topicReadable of topic in dialogTable of noun;
	say "[reply entry][line break]" as noun;
	if there is a post entry:
		postconditions post entry;
	checkState;
	
[redirect the talking action to asking, not sure why the regular way dont work]
Talking to is an action applying to one visible thing and one topic.
Understand "talk to [someone] about [text]" as talking to.
Instead of talking to a person:
	try asking noun about the topic understood

[The generalized listing topics to help players to know what to ask]
List topics is an action applying to one visible thing.
Understand "ask [someone]" as List topics.
Understand "talk to [someone]" as List Topics.

Instead of List topics a person:
	say "You can ask [the noun] about:[line break]";
	let N be 0;
	repeat through dialogTable of noun:
		if there is a topicReadable entry and there is a topic entry and preconditions pre entry:
			Now N is N + 1;
			say "    [topicReadable entry].";
	if N is 0:
		say "Nothing, they dont want to talk to you."

[Checks if the preconditions are set for a dialogue]			
To decide if preconditions (variablelist - list of text):
	Repeat with variable running through variablelist:
		if variable is unset:
			Decide on false;
	Decide on true;
	
To postconditions (variablelist - list of text):
	Repeat with variable running through variablelist:
		set variable;
		
Book 2 - extra actions and things?

Section 1 - signs

[import debug statement here, I am defining that a book is a thing right here.]
A sign is a kind of thing.

looking at is an action applying to one thing.
Understand "look at [a thing]" as looking at.

after looking at a sign:
	say "you read [the noun].";
	
Section 2 - items

An item is a kind of thing.

Book 3 - Rules and Tables of Logic

[ideally these would be automatically compiled from all the logic state sources (currently only dialogue tables)]

Table of state variables
key	value
"dead"	false
"printInfo"	true
"error"	false
with 50 blank rows

[getters]
To decide if (varName - text) is set:
	ensure varName exists;
	Choose a row with key of varName in the Table of state variables;
	Decide on whether or not value entry is true;
	
To decide if (varName - text) is unset:
	ensure varName exists;
	Choose a row with key of varName in the Table of state variables;
	Decide on whether or not value entry is false;

[setters]
To set (varName - text):
	ensure varName exists;
	Now the value corresponding to a key of varName in the Table of state variables is true;
	
To unset (varName - text):
	ensure varName exists;
	Now the value corresponding to a key of varName in the Table of state variables is false;
	
[all variables are initially considered to be unset if not in the table,
This ensures that there is no runtime error when trying to access a variable
This dynamic state variable behavior is also why we need those getters and setters.]
To ensure (varName - text) exists:
	Let entry exists be false;
	Repeat through the Table of state variables:
		if key entry is varName:
			now entry exists is true;
			break;
	if entry exists is false:
		Choose a blank row in Table of state variables;
		now key entry is varName;
		now value entry is false;

[an attempt to figure out all the state variables from dialogue]
When play begins:
	Repeat with person running through list of all people:
		Repeat through dialogTable of person:
			if there is a pre entry:
				Repeat with variable running through pre entry:
					ensure variable exists;
			if there is a post entry:
				Repeat with variable running through post entry:
					ensure variable exists;
					
Book 4 - a bit about directions

Definition: a direction (called thataway) is viable: 
	if the door thataway from the location is locked:
		decide no;
	if the room thataway from the location is a room:
		decide yes;
	decide no;


Volume 2 - Game Specific Stuff

Book 1 - The Town

Chapter 1 - Room definitions and links

Town Square is a room. "An open area for people to gather and do things together."
The Forest is a room. "The forest north of town."
The shopping district is a room. "People be shopping."
The North Road is a room. "the North Road."
[The South Road is a room.
The river is a room.]
The Side Alley is a room. "A sneaky side alley for sneaky people."
The Back Alley is a room. "A clever little hidden part of the town."
The Housing District is a room.

[town link definitions]
The North Road is north of Town Square. 
The forest is north of the North Road.
The side alley is west of town square.
the back alley is north of the side alley.
The shopping district is east of the North Road and north of The Housing District.
The Housing District is east of the town square.
[The river is south of the South Road.
The South Road is south of town square.
The fancy eatery is west of the south road.
The garbage dump is east of the south road.]

[test code for doors and keys which is also an item]
The heavy iron door is west of the north road and east of the back alley. heavy iron door is a locked door.
the matching key of the heavy iron door is heavy iron key.
there is a heavy iron key in the north road. heavy iron key is an item.

after unlocking heavy iron door with heavy iron key:
	say "the key dissolves.";
	now heavy iron key is nowhere;

Chapter 2 - People definitions

[Inside the Town Square is the player. [THIS IS WHERE THE PLAYER IS]]
Inside the North Road is the player. [THIS IS WHERE THE PLAYER IS]

Inside the shopping district is a merchant. 
The merchant is a person.

A Guard is in the north road. 
The guard is a person. 
The dialogTable of the guard is Table of Guard Dialog.

A clown is in the north road. 
The clown is a person.
The dialogTable of the clown is Table of Clown Dialog.	

A vagabond is in the Back Alley. 
The vagabond is a person. "You see a vagabond, an aimless traveler.".
the dialogTable of the vagabond is Table of vagabond dialog.


An Old Lady is in the Housing District. 
The Old Lady is a person. "An old lady with a quest for you.".
The dialogTable of the Old Lady is Table of old lady dialog.
The Old Lady is carrying a large portrait. 

The large portrait is a thing. 
The large portrait has a description "A large portrait of a quest colored cat.".

Chapter 3 - Items

	
the old cat is nowhere. The old cat is an item.
The necronomicon ad is in the shopping district. The necronomicon ad is a sign.
[The Thief's Guide to Stealing is in the back alley. the Thief's Guide to Stealing is a book.]



Book 2 - game specific logic 

Chapter 1 - nothing for now
	
Chapter 2 - Specification of Logic

[Here is where some of the trackable game logic is specified]

To checkState:
	If "catForest" is set and "movedCat" is unset:
		moveCatForest;
		Set "movedCatForest";
		set "movedCat";
	If "catAlley" is set and "movedCat" is unset:
		moveCatAlley;
		Set "movedCatAlley"; 
		set "movedCat";
	If "catQuest" is set:
		if old lady has large portrait:
			say "Here, take this picture I have of my cat and see if anyone can recognize it." as the old lady;
			move large portrait to location;
			try taking large portrait;
	If "addDistraction" is set:
		[distract general;]
		say "we disabled distractions here because it needed to test.";
		unset "addDistraction";
	If "completed" is set:
		set "catTaken";
		
To moveCatForest:
	Move the old cat to the forest;
		
To moveCatAlley:
	Move the old cat to the side alley;
	
After taking the old cat:
	set "catTaken";
	
After dropping the old cat:
	unset "catTaken";
	

	
Chapter 3 - Dialog States?

[ideally, these would be defined with the characters rather than down here, 
but for testing it is too useful to keep them together]

[The clown is here to test dialog features]
Table of Clown Dialog
topic	topicReadable	pre	post	reply
"honk" or "honkhonk"	"honk"	{}	{"clownTalked"}	"honk"
["distract"	"distract"	{}	{"addDistraction"}	"Done"]
"itself"	"itself"	{}	{"clownTalked"}	"I guess I am just a clown, nameless, thoughtless, doing nothing but hanging around"
--	"default"	{}	{"clownTalked"}	"As [the noun], I do not think you are entitled to a response about [the topic understood]. Now go away."

Table of Guard Dialog
topic	topicReadable	pre	post	reply
"the cat"	"the cat"	{"catQuest"}	{"catForest"}	"I have seen a cat running around here. Quest colored too. Try looking in the forest."
"a cat"	--	{"catQuest"}	{"catForest"}	"I have seen a cat running around here. Quest colored too. Try looking in the forest."
"the gate"	"the gate"	{}	{"guardTalked"}	"I am in charge of opening the gate in the morning and closing it at night."	
--	"default"	{}	--	"I have no idea what [a topic understood] is, I just guard the gate."

Table of old lady dialog
topic	topicReadable	pre	post	reply
"cat"	"her cat"	{}	{"catQuest"}	"Yes, take this picture of my cat and find it for me."
"unset"	"unset"	{}	--	"Error: missing dialog."
--	"default"	{}	{"catQuest"}	"I need you to help me find my cat."

Table of vagabond dialog
topic	topicReadable	pre	post	reply
"the cat"	"the cat"	{"catQuest"}	{"catAlley"}	"it is in the alley up there"


Table of passerby dialog
topic	topicReadable	pre	post	reply
"distract"	"distract"	{}	{"addDistraction"}	"Done"

Chapter 10 - winning

[instead of giving the old cat to the old lady:
	set "completed";
	printInfo;
	end the story finally saying "You have succeeded.";]


Volume 100 - Debug stuff - Not for release

Chapter - Policy Commands

[This chapter just details the tables that are associated with the current quest. Since each step of the quest is a discrete action we can just list the minimum steps that need to be done and a bit of extra info on how to get there and how to interact with (which is info the player normally would have to find out via investigation and wandering) to create commands that will guarantee a next step to complete the quest]

Table of required steps
Place	subject	Action	isDone	Completed
Housing District	Old Lady 	"talk to old lady about her cat"	{"catQuest"}	false
North Road	Guard	"talk to Guard about the cat"	{"catForest"}	false
Forest	Old Cat	"pick up old cat"	{"catTaken"}	false
Housing District	Old Lady	"give old lady the old cat"	{"completed"}	false


Table of required alley steps
Place	subject	Action	isDone	Completed
Housing District	Old Lady 	"talk to old lady about her cat"	{"catQuest"}	false
Back Alley	vagabond	"talk to vagabond about the cat"	{"catAlley"}	false
Side Alley	Old Cat	"pick up old cat"	{"catTaken"}	false
Housing District	Old Lady	"give old lady the old cat"	{"completed"}	false

Chapter - Drama Manager Actions

Debugging is an action applying to nothing.
Understand "debug" as debugging.

Section - moving things around

Moving something is an action applying to a thing and a thing.
Understand "DM move [something] to [any room]" as moving something.

Instead of moving something:
	Now turn count is turn count - 1;
	Now the noun is in the second noun;
	
Section - dealing with doors

Super unlocking is an action applying to a thing.
Understand "DM unlock [any door]" as super unlocking.

Instead of super unlocking:
	now the noun is unlocked;
	
Super locking is an action applying to a thing.
Understand "DM lock [any door]" as super locking.

Instead of super locking:
	now the noun is locked;

Section - distract

[todo: should redesign how the distraction stuff works to make the temp part easier]
[idea:
	distract me -> temp distract me
]

Chapter - print info

Section - text helpers

[fun text helpers including format a dict entry]
To decide which text is formatDictPair (key - text) - (value - text):
	decide on pairs properQuotes key - ":" - fixCaps value;
	
To decide which text is pairs (key - text) - (sep - text) - (value - text) :
	decide on "[key][sep] [value]";
	
To decide which text is properQuotes (v - value):
	let q be "[v]";
	if q matches the regular expression "'.*'":
		decide on q;
	decide on "'[q]'";

To decide which list of text is list_str (list_entries - list of objects):
	Let str_l be a list of text;
	repeat with i running from 1 to number of entries in list_entries:
		let str be fixCaps "'[entry i of list_entries]'";
		add str to str_l;
	decide on str_l;

[normalizes truthy values to -> true for json compat (removes quotes, fixes caps)]
[todo: honestly this would be easier as a table look up, may want to change to that]
To decide which text is fixCaps (printText - text):
	let truthy be "true";
	if printText is "'true'", decide on truthy;
	if printText is "true", decide on truthy;
	if printText is "'True'", decide on truthy;
	if printText is "True", decide on truthy;
	[]
	let falsey be "false";
	if printText is "'false'", decide on falsey;
	if printText is "false", decide on falsey;
	if printText is "'False'", decide on falsey;
	if printText is "False", decide on falsey;
	Decide on printText;
	
To decide which text is fixCaps (notText - value):
	decide on fixCaps "[notText]";
	
To decide which text is removeNothing (printText - text):
	if printText is "nothing", decide on "";
	decide on printText;

Section - printable data types

[format data types, mostly just using dict and list to keep with json standard]
To decide which text is formatTuple (iterable - list of text):
	decide on "([formatIterable iterable])"
	
To decide which text is formatList (iterable - list of text):
	decide on "[bracket][formatIterable iterable][close bracket]";
	
To decide which text is formatSet (iterable - list of text):
	decide on "{[formatIterable iterable]}";
	
To decide which text is formatDict (keys - list of text) - (values - list of text):
	decide on "{[formatIterable keys - values]}";
	
To decide which text is formatDictEntries (entries - list of text):
	decide on "{[formatIterable entries]}";

[format the iterables underlying those data types]
To decide which text is formatIterable (values - list of text):
	Let N be the number of entries in values;
	Let ret be "";
	If N is greater than 0:
		Let ret be "[entry 1 of values]";
	Repeat with i running from 2 to N:
		Let new_ret be "[entry i of values]";
		Let ret be "[ret], [new_ret]";
	decide on ret;

To decide which text is formatIterableNewlines (values - list of text):
	[a bad hack to turn an iterable into "infos" compatible text early. used for distractions]
	Let N be the number of entries in values;
	Let ret be "";
	If N is greater than 0:
		Let ret be "[entry 1 of values]";
	Repeat with i running from 2 to N:
		Let new_ret be "[entry i of values]";
		Let ret be "[ret], [line break][new_ret]";
	decide on ret;
	
To decide which text is formatIterable (keys - list of text) - (values - list of text):
	Let N be the number of entries in values;
	Let ret be "";
	If N is greater than 0:
		Let ret be pairs "[entry 1 of keys]" - ":" - "[entry 1 of values]";
	Repeat with i running from 2 to N:
		Let new_ret be pairs "[entry i of keys]" - ":" - "[entry i of values]";
		Let ret be "[ret], [new_ret]";
	decide on ret;

Section - addInfo Calls

[simplify the "add to info" calls for often used cases]
To decide which text is addInfoObjects (label - text) - (values - list of objects):
	decide on formatDictPair label - formatList list_str values;
	
To decide which text is addInfo (label - text) - (value - value):
	decide on formatDictPair label - properQuotes "[value]";
	
To decide which text is addActionInfo:
	let keys be a list of text;
	let v be a list of text;
	[]
	add properQuotes "subject" to keys;
	add properQuotes fixCaps removeNothing Action_subject to v;
	[]
	add properQuotes "object" to keys;
	add properQuotes fixCaps removeNothing Action_object to v;
	[]
	add properQuotes "verb" to keys;
	add properQuotes fixCaps removeNothing Action_verb to v;
	[]
	[add properQuotes "topic" to keys;
	add properQuotes fixCaps Action_understood to v;]
	decide on formatDictPair "'action'" - formatDict keys - v;
	
To decide which text is addStateVariables:
	let keys be a list of text;
	let v be a list of text;
	Repeat through Table of state variables:
		add properQuotes key entry to keys;
		add fixCaps value entry to v;
	decide on formatDictPair "'variables'" - formatDict keys - v;
	
To decide which text is addTalkInfo:
	let people_names be a list of text;
	let people_topics be a list of text;
	repeat with p running through withoutPlayer list of visible people:
		Let topic_list be a list of text;
		repeat through dialogTable of p:
			if there is a topicReadable entry and there is a topic entry and preconditions pre entry:
				add properQuotes topicReadable entry to topic_list;
		add properQuotes p to people_names;
		add formatList topic_list to people_topics;
	decide on formatDictPair "possible_talk" - formatDict people_names - people_topics;

Section - policy actions

To decide which text is addNextAction:
	[go through the Table of required steps and try to figure out which step we are on]
	[the step that we are on is the last step that is true which requires linear search]
	Repeat through the Table of required alley steps:
		unless preconditions isDone entry:
			decide on nextAvailableAction for action entry of subject entry in place entry;
			
To decide which text is addPolicyCommands:
	let v be a list of text;
	Repeat through the Table of required alley steps:
		unless preconditions isDone entry:
			add nextAvailableAction for action entry of subject entry in place entry to v;
	decide on formatList v;
	
to decide which text is nextAvailableAction for (action - text) of (subject - thing) in (requireLocation - room) :
	if subject is in location: [if we are in the same room, do the action]
		decide on "'[action]'";
	otherwise: [if not, go to the correct place]
		let direction be best route from location to requireLocation;
		decide on "'go [direction]'";
	
Section - Error stuff - not even remotely well done or complete

[here we try to detect an error of some sort and then just set a variable to indicate that this is probably not a valid action.]
To reset error info:
	unset "error";
	unset "errorClarify";
	
[before does the player mean:
	say "smoething"; ]
	
before clarifying the parser's choice:
	set "error";
	set "errorClarify";
	Continue the activity;
	
after Asking which do you mean:
	set "error";
	set "errorClarify";
	Continue the activity;
	
After printing a parser error:
	set "error";
	Continue the activity;
			
Section - action recording

[This helps the drama manager to figure out which action was taken. If no action is taken in a turn]

Action_subject is a text that varies.
Action_object is a text that varies.
Action_verb is a text that varies.
Action_understood is a text that varies.

To update action info (current action - action):
	if "action recorded" is unset:
		set "action recorded";
		now action_subject is "[noun part of current action]";
		now Action_object is "[second noun part of current action]";
		now Action_verb is "[action name part of current action]";
		[we cannot recover this because it is not always present, and when its missing it runtime errors]
		[now Action_understood is "[the topic understood]";]
		[showme Action_understood]
	
To reset action info:
	now action_subject is "";
	now Action_object is "";
	now Action_verb is "";
	now Action_understood is "";
	unset "action recorded";
		
before doing something to something:
	update action info current action;
	continue the action;

Section - compound lists (of distractions)

[first two are not used currently, keeping just in case...]
To decide which list of things is joinList (l1 - list of things) - (l2 - list of things):
	let p be a list of things;
	add l1 to p;
	add l2 to p;
	decide on p;
	
To decide which list of things is flattenList (l - list of list of things):
	let p be a list of things;
	repeat with l_i running through l:
		add l_i to p;
	decide on p;
	
to decide which list of things is withoutPlayer (l - list of things):
	if the player is listed in l:
		remove player from l;
	decide on l;
	
Section - printInfo

[A small section to fix the prompt given how we need to do some stuff]
When play begins: now the command prompt is "".

To printInfo (infos - list of text):
	say "INFO[line break]";
	repeat with info running through infos:
		say "[info][line break]";
	say "END INFO[line break]";

[all debug info is a single dict on a single line starting with "INFO" and ending with "END INFO"]
To printInfo (info - text):
	say "INFO[line break]";
	say "[info][line break]";
	say "END INFO[line break]";
	
To printInfoDictEntriesNewlines (infos - list of text):
	say "[line break]INFO[line break]";
	say "{";
	Let N be the number of entries in infos;
	Repeat with i running from 1 to N - 1:
		let info be entry i of infos;
		say "[info],[line break]";
	say "[entry N of infos]}[line break]";
	say "END INFO[line break]";
	
[TODO: This needs to be moved into the distractions generator python file]
[To decide which text is printActionables:
	let infos be a list of text;
	add addInfoObjects "distractions" - list of distracting things that are visible to infos;
	add addInfoObjects "distract_0_thing" - list of visible distract_0_thing to infos;
	decide on formatIterableNewlines infos;]

To printInfo:
	if "printInfo" is set:
		Let infos be a list of text;
		add addInfo "turnCount" - turn count to infos;
		add addInfo "score" - score to infos;
		add addInfo "location" - location to infos;
		[]
		add addInfoObjects "entities" - withoutPlayer list of things that are visible to infos;
		add addInfoObjects "inventory" - list of things carried by the player to infos;
		[]
		add addInfoObjects "viable_directions" - list of viable directions to infos;
		add addInfoObjects "unlocked_exits" - list of visible unlocked doors to infos;
		add addInfoObjects "locked_exits" - list of visible locked doors to infos;
		[]		
		add addInfoObjects "people" - withoutPlayer list of visible people to infos;
		add addInfoObjects "signs" - list of visible signs to infos;
		add addInfoObjects "items" - list of visible items to infos;
		add printActionables to infos;
		[]
		add addActionInfo to infos;
		add addStateVariables to infos;
		add addTalkInfo to infos;
		[]
		add addInfo "next_action" - addNextAction to infos;
		add addInfo "policy_commands" - addPolicyCommands to infos;
		[sort infos;]
		[printInfo infos;]
		[add addInfo "error" - error to infos;]
		[]
		printInfoDictEntriesNewlines infos;
		reset action info;
		reset error info;
		if command prompt is "":
			say "[line break]";
			say ">";
		
	
To InfoHelper:
	if "completed" is unset:
		printInfo;
	
Section - hacking together the DM info

When play begins:
	reset action info;

before Constructing the status line:
	InfoHelper;
	
