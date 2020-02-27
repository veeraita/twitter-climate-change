import sys
import tweepy
import time
import logging

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
    # create log file
    log_file_handler = logging.FileHandler('logfile.log')
    formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)
    # Gets or creates a logger
    logger = logging.getLogger(__name__)  
    # add file handler to logger
    logger.addHandler(log_file_handler)
    # Logs
    """
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('Something is not right.')
    logger.error('A Major error has happened.')
    logger.critical('Fatal error. Cannot continue')
    """
    # read settings file
    sts = Settings(args,log_file_handler)
    # decrypt twitter credentials
    ch = CredentialHandler(sts.credentialsfile, log_file_handler)
    # create streamlistener
    streamer = Streamer(sts.json_dump, log_file_handler)
    # start streaming
    stream = tweepy.Stream(auth=ch.get_auth(), listener=streamer,tweet_mode='extended')
    
    while True:
        try:
            stream.filter(track = sts.get_keywords(), locations=sts.location)
            print("looping too much?")
            #stream.sample()# Test maximum rates
        except Exception as ex:
            print(ex)
            waittime = 5
            print("Returning to stream after ",waittime, " seconds")
            time.sleep(waittime)

# run application
if __name__ == "__main__":
    
    # define file handler and set formatter
    
    main()