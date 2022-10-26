# MAB-PM-Recovery

This repository serves as a snapshot of the MAB player model recover project (paper title: "Using Multi-Armed Bandits to Dynamically Update Player Models in an Experience Managed Environment"). It is not completely in working order, but with the instructions below should be able to be reproducible.

## Instructions to Run

First the prerequisite libraries need to be installed (in requirements.txt), most notable textworld. Textworld requires a linux-like environment to run in such as WSL or linux.

The file needed to recreate the data is `run_all_scenarios.py` which when run will run all the scenarios against each other. This took around 2-3 days to complete on my machine as there are 50 trials, 20 scenarios (5 preferences against the other 4 preferences), and 6 agents, totaling in 6000 runs and each run takes something like 30 seconds or so to complete. This long runtime is due to the program loading up and running an actual inform7 game each time, which as you can imagine is not fast, nor is it running in WSL, and there are probably plenty of performance optimizations that I have just missed.

After running the program, you should end up with data in the `output_data` directory. This data is unfortunately very uncompressed as that makes it easier to debug, but future revisions (not in this repository) will attempt to make this less painful to move around. This is also why the data is not uploaded to this repository. The data should be stored in a directory named after the date when first ran.

To graph this data you need to head on over to graph_data.py and put the date of the date folder into these functions (found at the bottom of the py file) `cache_processing("output_data/2022-05-30")`, `final_graphs_and_chart("output_data/2022-05-30")`, `appendix_graphs("output_data/2022-05-30")` (currently filled in with the date folder that for our "final" run). The `cache_processing` function formats the data and runs a bunch of tests and writes that to file, `final_graphs_and_chart` generates the graphs (and the chart in mostly complete latex) from those files, and the `appendix_graphs` does the same but with all 20 individual scenarios instead of the grouped scenarios.

If anything does not work, or you have any trouble recreating this experiment please contact me, and I will help.

## WSL

I have had a lot of trouble installing the prerequisite stuff for WSL, so I will give a small writeup of what I found to be the best way here (mostly for me next time I want to set this up)

1. follow this guide to install wsl https://learn.microsoft.com/en-us/windows/wsl/install
- it should be about as easy as running `wsl --install` in cmd or powershell
- if you want to access the shell you can run wsl in cmd/powershell (or point your favorite terminal emulator to `C:/Windows/System32/wsl.exe` and maybe set the shell args to `~`).
2. the proper build tools are probably not installed, so before installing the python requirements you need to install that.
- run this command `sudo apt-get install build-essential` to install `make` and other essential things. Jericho, a prerequisite library, will not install without it.
3. you should now be able to install the requirements in the requirements.txt and run the program.
  
