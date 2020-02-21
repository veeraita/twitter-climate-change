import tweepy
import sys
import time

class Streamer(tweepy.StreamListener):
    def __init__(self, json_dump):
        """
        define output files here
        """
        self.json_dump = json_dump
        self.reconnection_attempts = 0 #count reconnection attempts
        self.reconnections_limit = 9
        super(Streamer,self).__init__()
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
        print("Encountered streaming error (", status_code, ")")
        print(self.reconnection_attempts," reconnection attempts.")

        if status_code in [420,429]: # rate limit exceeded
            # wait until rate limit is reset
            # NOTE API (created by credentialhandler) should take care of rate limits automatically
            time.sleep(15*60)
            self.reconnection_attempts += 1
        elif self.reconnection_attempts < self.reconnections_limit:
            # if there is some other error (internet connectione etc)
            wait_time = 2**self.reconnection_attempts
            print("Waiting ",wait_time, "s and reconnecting.")
            time.sleep(wait_time)
            self.reconnection_attempts += 1
            return True
        else:
            print("Reconnection attempts limit exceeded.")
            print("Terminating.")
            exit()

