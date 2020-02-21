import getpass 
import sys
import os
import tweepy
from cryptography.fernet import Fernet


class CredentialHandler:
    """
    Class for handling Twitter keys securely.
    Asks user for a password and decrypts credentials file.
    returns twitter api authentication
    """
    # TODO checkout https://stackoverflow.com/questions/42568262/how-to-encrypt-text-with-a-password-in-python
    def __init__(self, credentialsfile):
        """
        iostream: input / output stream created by ioHandler
        """
        self.credentialsfile = credentialsfile
        self.__set_credentials()
    def __set_credentials(self):
        """
        Asks user for encryption key
        """
        print("Type key for encrypted Twitter credentials file")
        print("You have tree attempts, after which the program terminates")
        for _ in range(3):
            try: 
                sys.stdout = open(os.devnull, "w") # switch off console output to suppress echo
                sys.stderr= open(os.devnull, "w")
                key = input(">>").encode()
                sys.stdout = sys.__stdout__ # restore echo
                sys.stderr = sys.__stderr__
                print(key)
                self.__decrypt(key)
            except Exception as error: 
                print('Invalid key. Please try again.', error) 
            else: 
                print('Valid password.') 
                return
        quit()
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
        decrypted = crypto.decrypt(token).decode().split()
        credentials = {}
        for i in range(4):
            credentials[decrypted[2*i]] = decrypted[2*i+1]
        auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
        auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
        # set api to wait and reconnect automatically in case of rate limit error
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
            
    def get_auth(self):
        return self.api.auth
        
