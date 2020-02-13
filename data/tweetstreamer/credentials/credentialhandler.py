import getpass 
from cryptography.fernet import Fernet


class CredentialHandler():
    """
    Class for handling Twitter keys securely.
    Asks user for a password and decrypts credentials file.
    """
    def __init__(self, credentialfile):
        """
        iostream: input / output stream created by ioHandler
        """
        self.credentialfile = credentialfile
        self.__credentials = {}
        self.__set_credentials()
    def __set_credentials(self):
        """
        Asks user for encryption key
        """
        print("Type key for encrypted Twitter credentials file")
        print("You have tree attempts, after which the program terminates")
        for _ in range(3):
            try: 
                key = getpass.getpass(prompt = ">>").encode()
                self.__decrypt(key)
            except Exception as error: 
                print('Invalid key. Please try again.', error) 
            else: 
                print('Valid password.') 
                return
        exit
    def __decrypt(self, key):
        """
        Read and decrypt password file

        decrypted format:

        consumer_key foostring
        consumer_secret foostring
        access_key foostring
        access_secret foostring
        """
        crypto = Fernet(key) # cryptography object
        f = open(self.credentialfile, mode= "rb")
        token = f.read()
        f.close()
        decrypted = crypto.decrypt(token).decode().split()
        for i in range(4):
            self.__credentials[decrypted[2*i]] = decrypted[2*i+1]
            
    def get_credentials(self):
        return self.__credentials.copy()
