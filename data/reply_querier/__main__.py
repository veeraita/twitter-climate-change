import sys
import tweepy
import time
import logging
import asyncio
import argparse

from datetime import datetime as dt
from packages.credentials import CredentialHandler
from packages.settings import Settings
from packages.reply_querier import ReplyQuerier,Io

def log_stats(start_time, MAX_C_TIMEOUTS, io, rquerier, n_timeouts):
    run_time = time.time()-start_time
    time_st  = time.strftime('%H hours %M minutes %S secs', time.gmtime(run_time))

    logging.info(':: ReplyQuerier SHUTDOWN INITIATED: Limit ({0}) of consequtive reconnection attempts reached.'.format(MAX_C_TIMEOUTS))
    logging.info(':: STATS: execution time {0:.0f} days, {1}'.format(run_time // (24*3600), time_st))
    logging.info('\tTweets processed {0}, replies found {1}'.format(io.process_count, rquerier.c_reply))
    logging.info('\tTotal number of reconnection timeouts: {0}'.format(n_timeouts))

async def main(args = None):

    N_SAVE_BATCH   = 10 # Default batch of processed tweets before save
    BASE_WAIT_TIME = 3
    MAX_WAIT_TIME  = 3600
    MAX_C_TIMEOUTS = 2
    
    debug_mode = False
    
    # stats
    start_time = time.time()
    # keep track of timeouts
    conseq_timeouts, n_timeouts = 0,0 

    """
    tweetReplyQuerier

    Application for querying and storing Reply data for set of tweets.
    """
    logging.info("AALTO LST Tweet ReplyQuerier\n\t")
    
    # define parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('settings_path', help="Setting path")
    parser.add_argument('-d', '--debug', action='store_true', help="uses debug mode")
    parser.add_argument('-k', '--keyfile', help="uses convenience method with separate Twitter credentials keyfile")
    
    args       = parser.parse_args()
    debug_mode = args.debug
    keyfile    = args.keyfile 
    logger     = logging.getLogger()
    logger.setLevel(logging.DEBUG) if debug_mode else logger.setLevel(logging.INFO) 

    # 1. read settings file
    sts = Settings(args.settings_path)

    # 2. decrypt and authenticate 
    cred_handler = CredentialHandler(sts.credentialsfile, keyfile)
    logging.info("Initialized successfully.\nStarting operation...")

    # instantiate Io module
    io = Io(sts.json_read_path, sts.json_write_path, sts.queried)
    
    
    while True:
        # instantiate replyquerier
        rquerier = ReplyQuerier(io, cred_handler, sts) 
        
        # block until complete, use flag to reset the number of 
        # conseq_timeouts variable in cases of consequtive timeout
        query_flag = False
        replies = await rquerier.fetch_replies(N_SAVE_BATCH, query_flag)
        logging.info("All tweets in {0} processed.".format(sts.json_read_path)) 
        
        if query_flag: conseq_timeouts = 0
        if len(replies) > 0:
            io.save(replies)
        
        if conseq_timeouts == MAX_C_TIMEOUTS:
            log_stats(start_time, MAX_C_TIMEOUTS, io, rquerier, n_timeouts)        
            break
        
        conseq_timeouts += 1
        n_timeouts += 1

        # set exp increasing waiting time
        iter_wait_time = BASE_WAIT_TIME**conseq_timeouts
        logging.info("Sleeping {0} s and retrying.".format(iter_wait_time))
        time.sleep(min(MAX_WAIT_TIME, iter_wait_time))
        
# run application
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())