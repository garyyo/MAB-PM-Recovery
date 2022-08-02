# MAB-PM-Recovery

This repository serves as a snapshot of the MAB player model recover project (paper title: "Using Multi-Armed Bandits to Dynamically Update Player Models in an Experience Managed Environment"). It is not completely in working order, but with the instructions below should be able to be reproducable.

## Instructions to Run

First the prerequisite libraries need to be installed (in requirements.txt), most notable textworld. Textworld requires a linux-like envirnoment to run in such as WSL or linux.

The file needed to recreate the data is `run_all_scenarios.py` which when run will run all the scenarios against each other. This took around 2-3 days to complete on my machine as there are 50 trials, 20 scenarios (5 prefs against the other 4 prefs), and 6 agents, totaling in 6000 runs and each run takes something like 30 seconds or so to complete. This long runtime is due to the program loading up and running an actual inform7 game each time, which as you can imagine is not fast, nor is it running in WSL, and there are probably plenty of performance optimizations that I have just missed.

After running you should end up with data in the `output_data` directory. This data is unfortunately very uncompressed as that makes it easier to debug, but future revisions (not in this repository) will attempt to make this less painful to move around. This is also why the data is not uploaded to this repository. The data should be stored in a directory named after the date when first ran.

To graph this data you need to head on over to graph_data.py and put the date of the date folder into these functions (found at the bottom of the py file) `cache_processing("output_data/2022-05-30")`, `final_graphs_and_chart("output_data/2022-05-30")`, `appendix_graphs("output_data/2022-05-30")` (currently filled in with the date folder that for our "final" run). The `cache_processing` function formats the data and runs a bunch of tests and writes that to file, `final_graphs_and_chart` generates the graphs (and the chart in mostly complete latex) from those files, and the `appendix_graphs` does the same but with all 20 individual scenarios instead of the grouped scenarios.

If anything does not work or you have any trouble recreating this experiment please contact me and I will help.
