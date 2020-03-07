import sys
import tweepy
import time
import logging
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
    logging.info('\tTweets processed {0}, replies saved {1}'.format(rquerier.process_count, io.c_saved))
    logging.info('\tTotal number of reconnection timeouts: {0}'.format(n_timeouts))

def main(args = None):

    N_SAVE_BATCH   = 1    # quota of replies kept in memory until next save 
    BASE_WAIT_TIME = 4    # high level wait time while reconnecting 
    MAX_QUERY_CHAR = 500
    MAX_C_TIMEOUTS = 9    # max number of timeouts
    MAX_WAIT_TIME  = 3600 # max wait time
    
    logging.basicConfig(
        filename="replyquerier.log",
        level=logging.DEBUG,
        format="%(asctime)s:%(levelname)s:%(message)s"
    )
    
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
    
    # parse parameters
    args       = parser.parse_args()
    debug_mode = args.debug
    keyfile    = args.keyfile 
    logger     = logging.getLogger('ReplyQuerier: Main')
    
    logger.setLevel(logging.DEBUG) if debug_mode else logger.setLevel(logging.INFO) 

    # 1. read settings file
    sts = Settings(args.settings_path)

    # 2. decrypt and authenticate 
    cred_handler = CredentialHandler(sts.credentialsfile, keyfile)
    logger.info("Initialized successfully.\nStarting operation...")

    # instantiate Io module
    io = Io(sts.json_read_path, sts.json_write_path, sts.queried, N_SAVE_BATCH)

    while True:
        # instantiate replyquerier
        rquerier = ReplyQuerier(io, cred_handler, sts, MAX_QUERY_CHAR) 
        
        # block until complete, use flag to reset the number of 
        # conseq_timeouts variable in cases of consequtive timeout
        query_flag = False
        rquerier.start_logic(query_flag)
        logging.info("All tweets in {0} processed.".format(sts.json_read_path)) 
        
        if query_flag: conseq_timeouts = 0

        if len(rquerier.output_stack) > 0:
            io.save(rquerier.output_stack)
        
        if conseq_timeouts == MAX_C_TIMEOUTS:
            log_stats(start_time, MAX_C_TIMEOUTS, io, rquerier, n_timeouts)        
            break
        
        conseq_timeouts += 1
        n_timeouts      += 1

        # set exp increasing waiting time
        iter_wait_time = BASE_WAIT_TIME**conseq_timeouts
        logging.info("Sleeping {0} s and retrying.".format(iter_wait_time))
        time.sleep(min(MAX_WAIT_TIME, iter_wait_time))
        
# run application
if __name__ == "__main__":
    main() # TODO: try speeding up the queries 
           # by using multiple async call instances with a shared io module 