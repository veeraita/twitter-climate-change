import sys
import tweepy
import time
import logging
import asyncio

from datetime import datetime as dt
from packages.credentials import CredentialHandler
from packages.settings import Settings
from packages.reply_querier import ReplyQuerier,Io

def main(args = None):

    N_SAVE_BATCH  = 10
    WAIT_TIME     = 5
    MAX_WAIT_TIME = 3600

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    """
    tweetReplyQuerier

    Application for querying and storing Reply data for set of tweets.
    """
    logging.info("AALTO LST tweetReplyQuerier\n")
    
    # local key import without encryption for conveniency, 
    # If you use this, remember to keep the credentials file in .gitignore
    keyfile = None
    if args is None:
        args = sys.argv[1] #settings file path
        if len(sys.argv) > 2:
            keyfile = sys.argv[2] #keyfile path
    
    # read settings file
    sts = Settings(args)

    # decrypt and authenticate 
    cred_handler = CredentialHandler(sts.credentialsfile, keyfile)
    logging.info("Initialized successfully.\nStarting operation...")

    connection_timeouts = 0
    while True:
        # instantiate Io module
        io = Io(sts.json_read_path, sts.json_write_path, sts.queried)

        # instantiate replyquerier
        rquerier = ReplyQuerier(io, cred_handler, sts) 
        
        # instantiate list for replies
        replies = []


        # block until complete
        query_flag = False

        # call is async as it uses generators + recursion
        await rquerier.get_all_replies(replies, N_SAVE_BATCH, query_flag)

        if query_flag: connection_timeouts = 0

        logging.info("All tweets in {0} processed.".format(sts.json_read_path)) 
        if len(replies) != 0:
            io.save(replies)
        
        # set exp increasing waiting time
        iter_wait_time = WAIT_TIME**connection_timeouts
        logging.info("Sleeping {0} s and retrying.".format(iter_wait_time))
        
        time.sleep(min(MAX_WAIT_TIME, iter_wait_time))
        connection_timeouts += 1
        

# run application
if __name__ == "__main__":
    main()