import getpass 

class CredentialHandler():
    """
    Class for handling Twitter keys securely.
    Asks user for a password and decrypts credentials file.
    """
    def __init__(iostream, credentialfile):
        """
        iostream: input / output stream created by ioHandler
        """
        self.iostream = iostream

    def __ask_password__():
        try: 
            p = getpass.getpass(prompt = "Credentials password", stream = self.iostream) 
        except Exception as error: 
            print('ERROR', error, file = "iostream") 
        else: 
            print('Password entered succesfully', file = iostream) 
            self.password = p
    def __decrypt__():
        """
        read and decrypt password file
        """
        pass
