import tweepy
import sys
import json
import time
import logging
import asyncio
from datetime import datetime as dt

class ReplyQuerier(tweepy.API):

    def __init__(self, io, cred_handler, sts):
        """
        define output files here
        """
        self.sts                   = sts
        self.io                    = io
        self.cred_handler          = cred_handler
        self.reconnection_attempts = 0 # count reconnection attempts
        self.reconnections_limit   = 9
        super(ReplyQuerier,self).__init__()

    
    def tweet_url(self, tweet):
        logging.debug("Tweet object in replyquerier.tweet_url():")
        logging.debug(tweet)
        return "https://twitter.com/{0}/status/{1}".format(tweet['user']['screen_name'], tweet['id'])

    def get_replies_to_tweet(self, origin_tweet):
        """Get replies to a given tweet. Recursive function."""

        WAIT_PERIOD = 60
        TWEET_COUNT = 100

        # shallow mechanism for dealing with mismatch of data types
        if type(origin_tweet) != dict: 
            origin_tweet = origin_tweet._json

        username = origin_tweet['user']['screen_name']
        origin_tweet_id = origin_tweet['id_str']

        logging.debug("Looking for replies to: {0}s".format(self.tweet_url(origin_tweet)))
        max_id = None

        while True:
            query = "to:{0}".format(username)
            
            # Query tweets that are directed to the user of the origin tweet 
            try:
                tweets = self.cred_handler.api.search(q=query, since_id=origin_tweet_id,
                                                    max_id = max_id, show_user=True, rpp=TWEET_COUNT) 

                logging.info("Successfully queried {0} tweets.".format(len(tweets)))
                logging.info('Potential replies fetched, inspect data.')

            except tweepy.error.TweepError as e:
                logging.error("Error: caught twitter api error while fetching the replies: %s", e)
                time.sleep(WAIT_PERIOD)
                continue
            
            for reply in tweets:
                logging.debug("Examining: %s" % self.tweet_url(reply._json))

                if str(reply.in_reply_to_status_id) == origin_tweet_id:
                    logging.info("Found a reply: %s" % self.tweet_url(reply._json))
                    yield reply
                    
                    # Recursive call for getting the chain of replies
                    # TODO: this recursive solution is modeled on: 
                    # https://gist.github.com/edsu/54e6f7d63df3866a87a15aed17b51eaf
                    # Recursion is error prone, and it would be good to deal with

                    for child_reply in self.get_replies_to_tweet(reply):
                        yield child_reply
                else:
                    logging.debug("not a reply, discarding.")
                max_id = reply.id
                
            if len(tweets) != TWEET_COUNT:
                break

    async def get_all_replies(self, replies, N_SAVE_BATCH, query_flag):
        
        # TODO: refactor to nicer format
        for i,tweet in enumerate(self.io.next_tweet()):
            logging.debug('Processing new tweet: {0}'.format(tweet))
            
            # calculate offset between current time and first tweet in the read data
            now_ts   = time.time()
            tweet_dt = dt.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
            offset   = now_ts - time.mktime(dt.timetuple(tweet_dt))
            
            # only fetch search if offset is bigger than the treshold
            if offset >= 3600*24*self.sts.time_treshold:        
                try:
                    # ensure that tweet has not already been queried
                    if tweet['id_str'] not in self.io.queried:
                        logging.debug("Tweet not in queried set, initializing query.")  
                        query_flag = True
                        
                        # instantiate query and iterate over the received generator object 
                        for reply in self.get_replies_to_tweet(tweet):
                            replies.append(reply._json)
                        
                        # add to the queried set                        
                        self.io.add_queried(tweet['id_str'])
                        
                        # save periodically (if batch size is full)
                        if i % N_SAVE_BATCH == 0:
                            if self.io.save(replies):
                                replies = []

                except Exception as ex:
                    logging.error(ex)
                    wait_time = 5
                    logging.info("Returning to tweet_data after {0} seconds".format(wait_time))
                    time.sleep(wait_time)
            else: 
                # Sleep until time treshold to maximize
                # the likelihood of the thread having closed
                hiber_time = 3600*24*self.sts.time_treshold - offset

                logging.info("All tweets within the time treshold have been processed.")
                logging.info("Sleeping until next tweet is over the time treshold.")
                logging.info("Process hibernates for {0:.0f} hours {1} minutes.".format(hiber_time / 3600, int(hiber_time) % 60))

                if len(replies) != 0:        
                    if self.io.save(replies):
                        replies = []
                    
                time.sleep(hiber_time)

        ready_flag = True