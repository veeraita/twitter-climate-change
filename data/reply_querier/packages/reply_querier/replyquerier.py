import tweepy
import sys
import json
import time
import logging
from datetime import datetime as dt

class ReplyQuerier(tweepy.API):
    """
    ReplyQuerier takes care of the application logic for conducting queries using 
    Twitter Search API, dependent on tweepy.

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
    def __init__(self, io, cred_handler, sts, reconn_limit = 9, MAX_QUERY_CHAR = 200):
        self.__query_len     = MAX_QUERY_CHAR
        self.__ids           = []
        self.__tweet_ids     = []
        self.__input_stack   = []

        self.output_stack    = []
        self.sts             = sts
        self.io              = io
        self.query_count     = 0
        self.reply_count     = 0
        self.process_count   = 0
        self.cred_handler    = cred_handler
        self.reconn_limit    = reconn_limit
        self.reconn_attempts = 0 # count reconnection attempts
        super(ReplyQuerier,self).__init__()

    def __tweet_url(self, screen_name, tweet_id_str):
        return "https://twitter.com/{0}/status/{1}".format(screen_name, tweet_id_str)

    def __generate_next_query(self):
        """Generates query from the tweets in the input stack."""
        query = ''
        tweets = []
        while len(self.__input_stack) > 0:
            tweet = self.__input_stack.pop()
            try:
                uname = tweet['user']['screen_name']
                is_seen = tweet['id_str'] in self.__tweet_ids or tweet['id_str'] in self.io.queried
                if not is_seen:
                    tmp_query = "to: {0}".format(uname) if query == '' else '{0} OR {1}'.format(query, uname)
                    if len(tmp_query) > self.__query_len: break
                    else: query = tmp_query 
                    tweets.append(tweet)

            except Exception as e:
                logging.info("(in __generate_next_query): No user info. Ignoring tweet.")
                continue 
        logging.info("Generated new query: {}".format(query))
        return query, tweets

    def __add_matching(self, tweets):
        for tweet in tweets:
            logging.info("Examining (in __add_matching method): {0}".format(self.__tweet_url(tweet.user.screen_name, tweet.id_str)))

            in_repl_to = str(tweet.in_reply_to_status_id)
            if in_repl_to is not None: 
                if (in_repl_to in self.__ids):
                    if (tweet.id_str not in self.io.queried or tweet.id_str not in self.__tweet_ids):
                        logging.info("\n:: HIT: Found a reply: {0} for: {1}".format(self.__tweet_url(tweet.user.screen_name, tweet.id_str),
                                                                                    self.__tweet_url(tweet.in_reply_to_screen_name, 
                                                                                                     tweet.in_reply_to_status_id_str)))    
                        self.__input_stack.append(tweet._json)      # add to tweets to be queried 
                        self.__ids.append(tweet.user.id_str)        # add to the "cache" for quick searchs
                        self.output_stack.append(tweet._json)       # keep note of output
                        self.reply_count += 1
                        logging.info('Added tweets to stack, reply count {}'.format(self.reply_count))
                    else: logging.info("Tweet already processed, discarding.") 
                else: logging.info("Not a reply to any known origin tweet, discarding.")
            else: 
                logging.debug("not a reply, discarding.")
            self.process_count += 1
            self.__tweet_ids.append(tweet.id_str) # Add tweet to already queried

    def __refill_stack(self, MIN_INPUT_STACK_SIZE, MAX_INPUT_STACK_SIZE):
        """Fills the input stack with new tweets from the original tweet file to ensure 
           that there is always enough available for the queries."""

        if len(self.__input_stack) <= MIN_INPUT_STACK_SIZE:
            while len(self.__input_stack) < MAX_INPUT_STACK_SIZE:
                self.__input_stack.append(next(self.io.next_tweet()))
    
    def __to_seconds(self, seconds):
        return seconds*3600*24    

    def get_replies_to_tweets(self, query, since_id, max_id):
        """Queries replies to a set of tweets using Search API."""
        
        WAIT_PERIOD    = 60
        MIN_QUERY_CHAR = 25
        # TWEET_COUNT    = 100
    
        # TODO: ensure proper type matching in the IO
        # # shallow mechanism for dealing with mismatch of data types
        # if type(origin_tweet) != dict: 
        #     origin_tweet = origin_tweet._json
        query_attempt = True
        while query_attempt:
            try:
                tweets = tweepy.Cursor(self.cred_handler.api.search, q = query, 
                                    since_id= since_id, max_id = max_id, 
                                    tweet_mode = 'extended').items() 
                
                self.query_count += 1
                tweets = [tweet for tweet in tweets] # from tweepy iterator to list

                logging.info("Successfully queried {0} tweets.".format(len(tweets)))
                logging.info('Potential replies fetched, tweets queued {}, inspecting data.'.format(len(self.__input_stack)))
                self.reconn_attempts = 0 # Zero reconn attempts
                query_attempt = False
                
            except tweepy.error.TweepError as e:
                logging.error(":: ERROR: caught twitter API exception while fetching the replies: %s", e)
                if '414' in repr(e): 
                    # In case of too long queries, trim the length of max query by one query (on avg 12 char)
                    self.__query_len = max(self.__query_len-12, MIN_QUERY_CHAR)

                self.reconn_attempts += 1
                time.sleep(WAIT_PERIOD*self.reconn_attempts)
                
                logging.info("Reconnection attempt # {0}.".format(self.reconn_attempts))

                if self.reconn_attempts == self.reconn_limit:
                    logging.error(':: TIMEOUT: Limit for reconnection attempt reached.')
                    raise
                continue

        # Inspect queried tweets and add matched to stack(s)
        self.__add_matching(tweets)

        # TODO: expand to also query parent tweets

        # Save periodically
        if len(self.output_stack) >= self.io.batch_size:
            logging.debug('Saving batch, {} tweets processed, {} saved.'.format(self.process_count, len(self.output_stack)))
                
            if self.io.save(self.output_stack):
                del self.output_stack  # free up memory
                self.output_stack = [] # re-init stack
        
    def __get_time_offset(self, tweets):
        """Returns the min time offset between current time and a set of tweets."""
        FROM    = '%a %b %d %H:%M:%S +0000 %Y'
        now_ts  = time.time()
        offset  = lambda x: now_ts - time.mktime(dt.timetuple(dt.strptime(x['created_at'], FROM)))
        timeset = map(offset, tweets)

        return min(timeset)     

    def start_logic(self, query_flag):
        """Logical process taking care of the fetching of replies."""
        MIN_INPUT_STACK_SIZE = 10
        MAX_INPUT_STACK_SIZE = 10 * MIN_INPUT_STACK_SIZE
        
        try:
            self.__refill_stack(MIN_INPUT_STACK_SIZE,MAX_INPUT_STACK_SIZE)
        except StopIteration as e:
            logging.info('No more blocks left in the read file: {}'.format(self.sts.json_read_path))

        while len(self.__input_stack) > 0:
        
            # calculate offset between current time and first tweet in the read data
            query, tweets = self.__generate_next_query()

            # keep note of which ids are searched for
            for tw in tweets:
                self.__ids.append(tw['id_str'])

            # limit the query to [since_id, max_id] to filter out unneccessary tweets
            since_id = min(tweets, key=lambda x: x['id'])['id']
            
            # max_id   = max(tweets, key=lambda x: x['id']) 
            max_id = None
            offset = self.__get_time_offset(tweets)
            
            # only fetch search if offset is bigger than the treshold
            if offset >= self.__to_seconds(self.sts.time_treshold):
                for tw in tweets:
                    logging.info("Looking for replies to: {0}".format(self.__tweet_url(tw['user']['screen_name'], tw['id_str'])))

                check_queried = lambda x: x['id_str'] in self.io.queried
                in_queried = list(map(check_queried, tweets))  
                # ensure that tweet has not already been queried
                if not all(in_queried):
                    logging.info("Tweet not in queried set, initializing query.")  
                    # set query flag, allows the main() to reset reconn counter 
                    query_flag = True
                    # instantiate query  
                    self.get_replies_to_tweets(query, since_id, max_id)
                    # add to the queried set                        
                    self.io.add_queried(tweets)
                else: logging.info('Tweet already in queried set, ignoring.')
            else: 
                # Sleep until time treshold to maximize
                # the likelihood of discussion thread having closed
                hiber_time = 3600*24*self.sts.time_treshold - offset

                logging.info("All tweets within the time treshold have been processed.")
                logging.info("Waiting until next tweet is over the time treshold.")
                logging.info("Process hibernates for {0:.0f} hours {1} minutes.".format(hiber_time / 3600, int(hiber_time) % 60))

                if len(self.output_stack) > 0:        
                    if self.io.save(self.output_stack):
                        del self.output_stack
                        self.output_stack = []
                    
                time.sleep(hiber_time)

            try:
                self.__refill_stack(MIN_INPUT_STACK_SIZE,MAX_INPUT_STACK_SIZE)
            except StopIteration as e:
                logging.info('No more blocks left in the read file: {}'.format(self.sts.json_read_path))
