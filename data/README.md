## Data folder
This folder includes software / scripts related to data collection part of the project. 
* `tools/` includes `encryptcredentials.py` script by which one can encrypt one's `twitter credentials`. The resulting `.bin` file is used by the data collection scripts.
* Under `tweetstreamer` folder you will find the keyword-streaming sotfware, which you can run on server for long periods of time.
* Under `reply_querier` folder you will find the software for fetching replies to a set of original tweets. This will take the output file of the `tweetstreamer` and query replies for it, hence allowing exploring the network structure of the tweets more fully.  
* While developing scripts and notebooks locally, you can also keep your data in this folder. Just remember to append the path to the data files into `.gitignore`-file residing at the root of the repository. This way none of the data will end up in the gitlab server.  