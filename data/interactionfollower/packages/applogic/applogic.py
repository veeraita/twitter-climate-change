import tweepy
import time
import logging.config
import random

from ..exceptions import StreamOfflineException
from ..credentials import CredentialHandler
from ..statsmodule import StatsModule
from ..following import Follower
from ..settings import Settings
from ..io import Io

class AppLogic:
    def __init__(self,sts,logger,chs):
        self.rattempts = 0
        self.streams   = []
        self.followers = []
        self.ios       = []
        self.chs       = chs
        self.sts       = sts
        self.is_connecteds = [False for _ in range(len(chs))]
        self._initialize_logic(logger)
        self.range     = range(len(self.streams))

    def _initialize_logic(self,logger):
        # initialize required modules
        logger.info("Initializing modules...")       
        n_range = range(1,self.sts.n_inst+1)

        # initialize io modules
        for i,cnfg in zip(n_range, self.sts.configs):
            logger.debug('Initializing io module {0}...'.format(i))

            filter_flag = isinstance(cnfg['filter'], list)
            self.ios.append(Io(i,cnfg['name'],cnfg['input'],cnfg['output'],cnfg['filter_output'],filter_flag))
        
        # initialize credentialhandlers and decrypt (asks for passphrase)      
        for i,ch in zip(n_range, self.chs):
            logger.info('Authenticating instance {0}...'.format(i))
            ch.authenticate()

        for cnfg,io in zip(self.sts.configs, self.ios):
            logger.debug('Initializing StreamListener {0}...'.format(io.ID)) 
            self.followers.append(Follower(io, cnfg['filter']))

        logger.info('Initializing streaming modules...')       
        for i,ch,follower in zip(n_range,self.chs,self.followers):
            logger.debug('Initializing Stream object {0}...'.format(i)) 
            stream = tweepy.Stream(auth=ch.get_auth(), listener=follower,tweet_mode='extended')
            self.streams.append(stream)
    
    def _refresh_streams(self, logger):
        stime = time.time()
        mode_msg = None
        for cnfg,io,stream,i in zip(self.sts.configs, self.ios, self.streams, self.range):
            # start following
            if not self.is_connecteds[i]:
                if cnfg['mode'] == 'follow':
                    time.sleep(random.uniform(0.1, 1.5))
                    stream.filter(follow = io.inputs, languages=["en"], is_async=True)
                    mode_msg = 'ids followed'
                else:
                    stream.filter(track = io.inputs, languages=["en"], is_async=True)    
                    mode_msg = 'keywords tracked'
                logger.info('STREAM {0} successfully connected, number of {1}: {2}'.format(io.ID,mode_msg,len(io.inputs)))
                self.is_connecteds[i] = True
        return stime
    
    def _refresh_userids(self, logger):
        logger.info('Checking for new user ids...')
        for io,stream,i,cnfg in zip(self.ios,self.streams,self.range, self.sts.configs):
            if cnfg['mode'] == 'follow':
                if io.update():
                    logger.info('STREAM {0}: New user ids found. Disconnecting the stream.'.format(io.ID))
                    try:
                        stream.disconnect()
                        self.is_connecteds[i] = False
                    except Exception as ex:
                        logger.error('Disconnection failed.')
        
        if all(self.is_connecteds):
            logger.info('No new ids found.')

    def run(self,logger,stats):
        # app logic
        logger.info('Opening {0} streams.'.format(len(self.streams)))
        
        while True:
            try:
                # Check status of the streams, reconnect if necessary 
                stime = self._refresh_streams(logger)
                
                if all(self.is_connecteds): # If all streams are connected, zero rattempts
                    self.rattempts = 0
                
                # Log stats and refresh userids periodically
                offset = time.time() - stime
                time.sleep(self.sts.update_interval*60-offset)
                stats.log_stats()
                self._refresh_userids(logger)

            except StreamOfflineException as se:
                logger.error(repr(se))
                for i in self.range:
                    if str(i+1) in str(se):
                        self.streams[i].disconnect()
                        self.is_connecteds[i] = False
                        logger.info('Set stream {} status as disconnected.'.format(i+1))
                self.rattempts += 1
                waittime = min(2**self.rattempts,3600) # Max waiting time = 1 hour
                logger.info("Waiting %d seconds before attempting to open stream again",waittime)
                time.sleep(waittime)

            except Exception as ex:
                logger.error('Error: %s',repr(ex))
                # For general error disconnect all streams and reconnect after waiting
                for stream,io,i in zip(self.streams,self.ios,range(len(self.streams))):
                    stream.disconnect()
                    self.is_connecteds[i] = False
                    logger.error('STREAM {0} disconnected due to error.'.format(io.ID))
                self.rattempts += 1
                waittime = min(2**self.rattempts,3600) # Max waiting time = 1 hour
                logger.info("Waiting %d seconds before attempting to open streams again",waittime)
                time.sleep(waittime)
