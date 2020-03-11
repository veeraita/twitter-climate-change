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
    # log_file_handler = logging.FileHandler('logfile.log')
    # formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    # log_file_handler.setFormatter(formatter)
    # Gets or creates a logger
    logger = logging.getLogger()  
    logger.setLevel(logging.DEBUG)
    
    #logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    # add file handler to logger

    # logger.addHandler(log_file_handler)
    # Logs
    """
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('Something is not right.')
    logger.error('A Major error has happened.')
    logger.critical('Fatal error. Cannot continue')
    """
    logger.info("yay!")
    # read settings file
    sts = Settings(args)
    # decrypt twitter credentials
    ch = CredentialHandler(sts.credentialsfile)
    # authenticate by Tweepy OAuth2
    logging.info('Initializing auth')
    ch.authenticate()
    # create streamlistener
    streamer = Streamer(sts.json_dump)
    # create streaming object
    stream = tweepy.Stream(auth=ch.get_auth(), listener=streamer,tweet_mode='extended')
    # read keywords
    keywords = sts.get_keywords()
    while True:
        try:
            # start streaming
            logger.info('Opening a stream.')
            stream.filter(track = keywords)
        except Exception as ex:
            waittime = 5
            logger.error('Error: %s',repr(ex))
            logger.info("Waiting %d seconds before attempting to open a new stream",waittime)
            time.sleep(waittime)

# run application
if __name__ == "__main__":
    
    # define file handler and set formatter
    
    main()
