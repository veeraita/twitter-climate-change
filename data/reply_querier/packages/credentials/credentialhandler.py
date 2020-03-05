import getpass 
import tweepy
from cryptography.fernet import Fernet


class CredentialHandler:
    """
    Class for handling Twitter keys securely.
    Asks user for a password and decrypts credentials file.
    returns twitter api authentication
    """
    def __init__(self, credentialsfile, keyfile = None):
        """
        iostream: input / output stream created by ioHandler
        """
        self.credentialsfile = credentialsfile
        self.__keyfile = keyfile
        self.__set_credentials()
    def __set_credentials(self):
        """
        Asks user for encryption key
        """
        credentials = None
        for _ in range(3):
            if not self.__keyfile: 
                print("Type key for encrypted Twitter credentials file")
                print("You have tree attempts, after which the program terminates")
                try:
                    key = getpass.getpass(prompt = ">>").encode()
                    credentials = self.__decrypt(key)
                except Exception as error: 
                    print('Invalid key. Please try again.', error) 
                else: 
                    print('Valid password.') 
                    return
            else:
                f = open(self.__keyfile, mode= "rb")
                keys = [line.strip() for line in f.readlines()]
                f.close()
                
                credentials = self.__read_keyfile(keys)
                break
        
        self.__auth(credentials)
        
    def __read_keyfile(self, keys):
        credentials = {}
        keys_dec    = [key.decode('utf-8') for key in keys]
        credentials['consumer_key'], credentials['consumer_secret'] = keys_dec[0], keys_dec[1]
        credentials['access_token'], credentials['access_token_secret'] = keys_dec[2], keys_dec[3]
        
        return credentials

    def __decrypt(self, key):
        """
        Read and decrypt password file, authenticate tweepy api

        decrypted format:

        consumer_key foostring
        consumer_secret foostring
        access_key foostring
        access_secret foostring
        """
        crypto = Fernet(key) # cryptography object
        f = open(self.credentialsfile, mode= "rb")
        token = f.read()
        f.close()
        decrypted = crypto.decrypt(token).decode('utf-8').split()
        
        credentials = {}
        for i in range(4):
            credentials[decrypted[2*i]] = decrypted[2*i+1]
        
        return credentials

    def __auth(self, credentials):
        auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
        auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
        # set api to wait and reconnect automatically in case of rate limit error
    
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    def get_auth(self):
        return self.api.auth
        
