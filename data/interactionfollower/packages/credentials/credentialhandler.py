from getpass import getpass
import sys
import os
import base64
import tweepy
import logging.config
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CredentialHandler:
    """
    Class for handling Twitter keys securely.
    Asks user for a password and decrypts credentials file.
    returns twitter api authentication
    """
    
    def __init__(self, credentialsfile):
        """"""
        
        self.logger = logging.getLogger('CredentialHandler') 
        try:
            self.credentialsfile = credentialsfile
            self.__set_credentials()
        except Exception as ex:
            self.logger.error("Error while reading credentials: %s",repr(ex))
            self.logger.info("Exiting program.")
            exit()

    def __set_credentials(self):
        """
        Asks user for encryption key
        """
        print("**Credential decryption for file: {0}**\n ".format(self.credentialsfile))
        is_correct = False
        while not is_correct:
            try: 
                # Password
                password = getpass("Please enter the passphrase for decryption:\n")    # Reads what user inputs
                # print(f'You entered {password} and its type is {type(password)}')
                password = password.encode()
                # Encryption data
                salt = b'm\xe4\xfb\xaexB\x7f2\xaa\x1dj\x8c\x8f\xf1\\{'
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                is_correct, credentials = self.__decrypt(key)
                if is_correct:
                    self.credentials = credentials
                    self.logger.debug('Credentials read, calling back to main.')

                
            except Exception as error: 
                self.logger.error("Something went wrong during key derivation:{}".format(error)) 
            
    def __decrypt(self, key):
        """
        Reads and decrypts password file

        Decrypted format:
        ----------------
        consumer_key foostring
        consumer_secret foostring
        access_token foostring
        access_token_secret foostring
        ----------------
 
        """
        crypto = Fernet(key) # cryptography object
        
        with open(self.credentialsfile, mode= "rb") as f:
            token = f.read()
        
        try:
            decrypted = crypto.decrypt(token).decode().split()
            credentials = {}
            for i in range(0,8,2):
                credentials[decrypted[i]] = decrypted[i+1]
        except Exception as e:
            self.logger.error("Invalid password: {}".format(e))
            return False, None

        self.logger.info('Valid password.') 
        self.logger.info("Credentials read successfully.")
        return True, credentials

    def authenticate(self):
        """Authenticate Tweepy API"""
        
        auth = tweepy.OAuthHandler(self.credentials['consumer_key'], self.credentials['consumer_secret'])
        auth.set_access_token(self.credentials['access_token'], self.credentials['access_token_secret'])
        # set api to wait and reconnect automatically in case of rate limit error
        try:
            self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
            self.logger.info("Twitter authentication established successfully.")
        except Exception as e:
            self.logger.error("Authentication failed: {}".format(e))

    def get_auth(self):
        return self.api.auth
        
