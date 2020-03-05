import tweepy
import sys
import json
import time
import logging
from datetime import datetime as dt

class ReplyQuerier(tweepy.API):
    """
    ReplyQuerier class for querying the search API. Dependent on tweepy,
    outputs list of tweets.

    ...

    Attributes
    ----------
    io : Io
        Io module for I/O tasks.
    cred_handler : CredentialsHandler
        CredentialsHandler for authentication and api duties. 
    reconn_limit : int
        Set the limit for reconnections.
    
    """
    def __init__(self, io, cred_handler, sts, reconn_limit = 9):
        """
        define output files here
        """
        self.sts             = sts
        self.io              = io
        self.cred_handler    = cred_handler
        self.reconn_limit    = reconn_limit
        self.reconn_attempts = 0 # count reconnection attempts
        super(ReplyQuerier,self).__init__()
    
    def tweet_url(self, tweet):
        return "https://twitter.com/{0}/status/{1}".format(tweet['user']['screen_name'], tweet['id_str'])

    def get_replies_to_tweet(self, origin_tweet, replies):
        """Get replies to a given tweet. Recursive function."""
        
        WAIT_PERIOD = 60
        TWEET_COUNT = 100

        # shallow mechanism for dealing with mismatch of data types
        if type(origin_tweet) != dict: 
            origin_tweet = origin_tweet._json

        username = origin_tweet['user']['screen_name']
        origin_tweet_id = origin_tweet['id_str']
        max_id = None

        logging.info("Looking for replies to: {0}".format(self.tweet_url(origin_tweet)))

        while True:
            # Query tweets that are directed to the user of the origin tweet 
            try:
                tweets = tweepy.Cursor(self.cred_handler.api.search, 
                                       q="to:{0}".format(username), since_id=origin_tweet_id,
                                       max_id = max_id, tweet_mode='extended').items() 

                tweets = [tweet for tweet in tweets]
                logging.info("Successfully queried {0} tweets.".format(len(tweets)))
                logging.debug('Potential replies fetched, inspect data.')
                
                reconn_attempts = 0
            except tweepy.error.TweepError as e:
                logging.error(":: ERROR: caught twitter API exception while fetching the replies: %s", e)
                time.sleep(WAIT_PERIOD*self.reconn_limit)
                
                self.reconn_attempts += 1
                logging.info("Reconnection attempt # {0}.".format(self.reconn_attempts))
                if reconn_attempts == reconn_limit:
                    logging.error(':: TIMEOUT: Limit for reconnection attempt reached.')
                    raise
                continue
            
            for reply in tweets:
                logging.debug("Examining: {0}".format(self.tweet_url(reply._json)))

                if str(reply.in_reply_to_status_id) == origin_tweet_id:
                    logging.info("\n:: HIT: Found a reply: {0} for: {1}".format(self.tweet_url(reply._json), self.tweet_url(origin_tweet)))
                    replies.append(reply._json)
                    try:                    
                    # Recursive call for getting the chain of replies
                        for child_reply in self.get_replies_to_tweet(reply):
                            pass
                    except Exception:
                        pass
                else:
                    logging.debug("not a reply, discarding.")
                max_id = reply.id
                
            if len(tweets) != TWEET_COUNT:
                break

    def fetch_replies(self, N_SAVE_BATCH, query_flag):
        replies = []

        # For large
        for i,tweet in enumerate(self.io.next_tweet()):
            try: 
                logging.debug("\n\nInspecting tweet: %s" % self.tweet_url(tweet))
            except Exception:
                logging.error("Not a proper tweet object. Disgarding.")
                continue
            # calculate offset between current time and first tweet in the read data
            now_ts   = time.time()
            tweet_dt = dt.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
            offset   = now_ts - time.mktime(dt.timetuple(tweet_dt))
            
            # only fetch search if offset is bigger than the treshold
            if offset >= 3600*24*self.sts.time_treshold:        
                # ensure that tweet has not already been queried
                if tweet['id_str'] not in self.io.queried:
                    logging.debug("Tweet not in queried set, initializing query.")  
                    
                    # set query flag, allows the main() to reset reconn counter 
                    query_flag = True
                    
                    # instantiate query  
                    self.get_replies_to_tweet(tweet, replies)
                    
                    # add to the queried set                        
                    self.io.add_queried(tweet['id_str'])
                    
                    # save periodically (if batch size is full)
                    if i % N_SAVE_BATCH == 0:
                        logging.debug('Saving batch, {} tweets processed, {} saved.'.format(i,len(replies)))
                
                        if self.io.save(replies):
                            replies = []
                else: 
                    logging.debug('Tweet already in queried set, ignoring.')
                
            else: 
                # Sleep until time treshold to maximize
                # the likelihood of discussion thread having closed
                hiber_time = 3600*24*self.sts.time_treshold - offset

                logging.info("All tweets within the time treshold have been processed.")
                logging.info("Waiting until next tweet is over the time treshold.")
                logging.info("Process hibernates for {0:.0f} hours {1} minutes.".format(hiber_time / 3600, int(hiber_time) % 60))

                if len(replies) != 0:        
                    if self.io.save(replies):
                        replies = []
                    
                time.sleep(hiber_time)

        ready_flag = True
        return replies