import tweepy
import sys
import time
import logging
from datetime import datetime, timedelta
import string


class Streamer(tweepy.StreamListener):
    def __init__(self, json_dump, log_file_handler):
        """
        define output files here
        """
        # create new json dump file every day at certain hour
        #self.newfiletime = time0.replace(day=x.day, hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self.filetime = datetime.now()
        self.valid_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)
        
        # Gets or creates a logger
        self.logger = logging.getLogger(__name__) 
        self.logger.setLevel(logging.INFO) 
        # add file handler to logger
        self.logger.addHandler(log_file_handler)
        self.splittimeperiod = time
        try:
            self.json_dump = json_dump
            filename = "%s_%s.json"%(self.json_dump,str(self.filetime))
            self.jsonfilename = ''.join(c for c in filename if c in self.valid_chars)
            with open(self.jsonfilename, 'w+') as f:
                #create new file
                pass
            self.reconnection_attempts = 0 #count reconnection attempts
            self.last_reconnection_time = time.time()
            self.reconnections_limit = 9
            super(Streamer,self).__init__()
            #successfull initialization!
            self.logger.info("Streamer initialized successfully.")
        except Exception as ex:
            self.logger.error("Error: %s. Exiting program.",repr(ex))
            exit()
    def on_data(self,data):
        """
        Dumps everything to a file in json format
        """
        #reset reconnection attempts
        self.reconnection_attempts = 0
        timenow = datetime.now()
        
        if timenow >= self.filetime: #time to create new file
            self.filetime += timedelta(days=1, hours= 3) 
            filename = "%s_%s.json"%(self.json_dump,str(self.filetime))
            self.jsonfilename = ''.join(c for c in filename if c in self.valid_chars) #parse out not allowed characters
            with open(self.jsonfilename, 'w+') as f:
                #create new file
                pass

        with open(self.jsonfilename, "a") as f:
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
        self.logger.error("Encountered streaming error: %s",repr(status_code))
        self.logger.info("Reconnection attempts: %d",(self.reconnection_attempts))

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
        self.logger.info("Waiting %d s and reconnecting.",waittime)
        time.sleep(waittime)
        self.reconnection_attempts += 1
        self.last_reconnection_time = time.time()
        return True
        #else:
        #    print("Reconnection attempts limit exceeded.")
        #    print("Terminating.")
        #    exit()

