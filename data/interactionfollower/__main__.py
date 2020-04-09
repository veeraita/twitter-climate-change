import sys
import tweepy
import time
import logging.config
import random
from packages.exceptions import StreamOfflineException
from packages.credentials import CredentialHandler
from packages.statsmodule import StatsModule
from packages.following import Follower
from packages.applogic import AppLogic
from packages.settings import Settings
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

def initialize_credentials(sts, logger):
    chs = [] 
    n_range = range(1,sts.n_inst+1)
    for i,cnfg in zip(n_range, sts.configs):
        logger.debug('Initializing CredentialHandler {0}...'.format(i)) 
        chs.append(CredentialHandler(cnfg['credentials']))  
    return chs

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

    # Initialize credentials
    logger.info('Reading credentials')
    chs = initialize_credentials(sts,logger)

    # Initialize app logic
    logic = AppLogic(sts,logger,chs)
    
    # initialize stats
    stats = StatsModule(logic.ios, UPDATE_INTERVAL)
    
    while True:
        try:
            # run the app logic
            logic.run(logger,stats)
        except Exception as ex:
            #  Executes "hard" restart of the logic in case exception
            #  escapes from the AppLogic module, keeps statistics as is
            logger.error('Unknown exception occurred,', repr(ex))
            logger.warning('Restarting application logic!')
            logic = AppLogic(sts,logger,chs)
            stats.change_ios(logic.ios)

# run application
if __name__ == "__main__":
    main()
