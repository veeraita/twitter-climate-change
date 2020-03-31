import sys
import tweepy
import time
import logging.config

from packages.credentials import CredentialHandler
from packages.following import Follower
from packages.settings import Settings
from packages.statsmodule import StatsModule
from packages.io import Io

def initialize_logging(sts): 
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'debug_handler': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': '{0}.debug'.format(sts.logfile),
                'encoding': 'utf8'
            },
            'default_handler': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'filename': '{0}.info'.format(sts.logfile),
                'encoding': 'utf8'
            },
        },
        'loggers': {
            '': {
                'handlers': ['debug_handler','default_handler'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }
    logging.config.dictConfig(logging_config)
    return logging.getLogger("TweetStreamer AppLogic (MAIN)")

def initialize(sts,logger):
    # initialize required modules
    logger.info("Initializing modules...")
    streams, ios, chs, followers = [], [], [], []
    n_range = range(1,sts.n_inst+1)

    # initialize io modules
    for i,cnfg in zip(n_range, sts.configs):
        logger.debug('Initializing io module {0}...'.format(i))
        if cnfg['filter_output']:
            ios.append(Io(i,cnfg['input'],cnfg['output'],cnfg['filter_output']))
        else:
            ios.append(Io(i,cnfg['input'],cnfg['output'],cnfg['filter_output']))
    
    
    # initialize credentialhandlers and decrypt (asks for passphrase)
    logger.info('Reading credentials')
    for i,cnfg in zip(n_range, sts.configs):
        logger.debug('Initializing CredentialHandler {0}...'.format(i)) 
        chs.append(CredentialHandler(cnfg['credentials']))        
    
    for i,ch in zip(n_range, chs):
        logger.info('Authenticating instance {0}...'.format(i))
        ch.authenticate()

    for cnfg,io in zip(sts.configs,ios):
        logger.debug('Initializing StreamListener {0}...'.format(io.ID)) 
        followers.append(Follower(io, cnfg['filter']))

    logger.info('Initializing streaming modules...')       
    for i,ch,follower in zip(n_range,chs,followers):
        logger.debug('Initializing Stream object {0}...'.format(i)) 
        stream = tweepy.Stream(auth=ch.get_auth(), listener=follower,tweet_mode='extended')
        streams.append(stream)
    
    return streams, ios, chs, followers

def main(args = None):
    """
    TweetStreamer

    Application for storing Twitter streaming data
    """

    print("AALTO LST TweetStreamer\n")
    if args is None:
        SETTINGS_FILENAME = sys.argv[1] #settings file name
    
    # read settings file
    sts = Settings(SETTINGS_FILENAME)
    UPDATE_INTERVAL = sts.update_interval # Will be same for all

    # Initialize logging
    logger = initialize_logging(sts)
    
    # Initialize objects
    streams, ios, chs, followers = initialize(sts,logger)
    time.sleep(0.2)
    stats = StatsModule(ios, UPDATE_INTERVAL)
    
    # app logic
    is_connecteds = [False for _ in range(len(streams))]
    logger.info('Opening {0} streams.'.format(len(streams)))
    reconnection_attempts = 0
    while True:
        try:
            stime = time.time()

            mode_msg = None
            for cnfg,io,stream,i in zip(sts.configs, ios, streams, range(len(streams))):
                # start following
                if not is_connecteds[i]:
                    if cnfg['mode'] == 'follow':
                        stream.filter(follow = io.inputs, languages=["en"], is_async=True)
                        mode_msg = 'ids followed'
                    else:
                        stream.filter(track = io.inputs, languages=["en"], is_async=True)    
                        mode_msg = 'keywords tracked'
                    logger.info('STREAM {0} successfully connected, number of {1}: {2}'.format(io.ID,mode_msg,len(io.inputs)))
                    is_connecteds[i] = True
            reconnection_attempts = 0

            # Log and refresh userids periodically
            time.sleep(UPDATE_INTERVAL*60-(time.time() - stime))
            stats.log_stats()
            
            logger.info('Checking for new user ids...')
            for io,stream,i,cnfg in zip(ios,streams,range(len(streams)), sts.configs):
                if cnfg['mode'] == 'follow':
                    if io.update():
                        logger.info('STREAM {0}: New user ids found. Disconnecting the stream.'.format(io.ID))
                        try:
                            stream.disconnect()
                            is_connecteds[i] = False
                        except Exception as ex:
                            logger.error('Disconnection failed.')
            
            if all(is_connecteds):
                logger.info('No new ids found.')

        except Exception as ex:
            logger.error('Error: %s',repr(ex))
            # Error encountered disconnect all streams and reconnect after waiting
            for stream,io,i in zip(streams,ios,range(len(streams))):
                stream.disconnect()
                is_connecteds[i] = False
                logger.error('STREAM {0} disconnected due to error.')
            reconnection_attempts += 1
            waittime = min(2**reconnection_attempts,3600) # Max waiting time = 1 hour
            logger.info("Waiting %d seconds before attempting to open streams again",waittime)
            time.sleep(waittime)

# run application
if __name__ == "__main__":
    # define file handler and set formatter
    main()
