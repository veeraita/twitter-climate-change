import sys
import tweepy
from .credentials import CredentialHandler
from .settings import Settings
from .streaming import Streamer
def main(args = None):
    """
    tweetstreamer

    Application for storing Twitter streaming data
    """
    print("AALTO LST tweetstreamer\n")
    if args is None:
        args = sys.argv[1] #settings file name
    # read settings file
    sts = Settings(args)
    # decrypt twitter credentials
    ch = CredentialHandler(sts.credentialsfile)
    # create streamlistener
    streamer = Streamer(sts.json_dump, sts.csv_out)
    # start streaming
    stream = tweepy.Stream(auth=ch.get_auth(), listener=streamer,tweet_mode='extended')
    stream.filter(track = sts.get_keywords(), locations=sts.location)

# run application
if __name__ == "__main__":
    main()