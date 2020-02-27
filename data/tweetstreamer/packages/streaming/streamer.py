import tweepy
import sys
import time
import logging

class Streamer(tweepy.StreamListener):
    def __init__(self, json_dump, log_file_handler):
        """
        define output files here
        """
        # Gets or creates a logger
        self.logger = logging.getLogger(__name__)  
        # add file handler to logger
        self.logger.addHandler(log_file_handler)
        try:
            self.json_dump = json_dump
            self.reconnection_attempts = 0 #count reconnection attempts
            self.last_reconnection_time = time.time()
            self.reconnections_limit = 9
            super(Streamer,self).__init__()
            #successfull initialization!
            self.logger.info("Streamer initialized successfully.")
        except Exception as ex:
            self.logger.error("Error: %s. Exiting program."%ex)
            exit()
    def on_data(self,data):
        """
        Dumps everything to a file in json format
        """
        self.reconnection_attempts = 0
        with open(self.json_dump, "a") as f:
            f.write(data)
            return
    def on_error(self, status_code):
        """
        twitter recommends immediate reconnection attempt with exponential wait pattern>
        1. attempt to reconnect
        2. wait 1,2,4,8, limit seconds
        3. if limit exceeded, terminate program and notify user

        returning True reconnects the stream

        if disconnection is due to exceeded rate limit, 
        reset shoulf be waited for or the app might get blacklisted
        (API should take care of this)

        http://docs.tweepy.org/en/latest/streaming_how_to.html
        """
        self.logger.error("Encountered streaming error: %s"%str(status_code))
        self.logger.info("Reconnection attempts: %s"%str(self.reconnection_attempts))

        waittime = 2**self.reconnection_attempts
        if status_code in [420,429]: # rate limit exceeded
            # wait until rate limit is reset
            # NOTE API (created by credentialhandler) should take care of rate limits automatically
            self.logger.warning("Rate limit exceeded.")
            waittime = 60*15
        # if there is some other error (internet connectione etc)
        if time.time() >= self.last_reconnection_time + 60*60*2:
            # null counter if two hours since last reconnection
            self.reconnection_attempts = 0
            self.logger.info("Over two hours since the last reconnection. Nullified reconnection attempt count.")
        self.logger.info("Waiting %d s and reconnecting."%waittime)
        time.sleep(waittime)
        self.reconnection_attempts += 1
        self.last_reconnection_time = time.time()
        return True
        #else:
        #    print("Reconnection attempts limit exceeded.")
        #    print("Terminating.")
        #    exit()

