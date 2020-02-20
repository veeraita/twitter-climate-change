import sys
import tweepy


from packages.credentials import CredentialHandler
from packages.settings import Settings
from packages.streaming import Streamer

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
    #stream.filter(track = sts.get_keywords(), locations=sts.location)
    stream.sample()# Test maximum rates

# run application
if __name__ == "__main__":
    main()