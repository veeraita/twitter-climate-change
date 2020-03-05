import sys
import base64
from getpass import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def main(filename = None):
    try:
        if filename is None:
            filename = sys.argv[1]
        # read file contents
        f = open(filename, "rb") #read in binary
        blines = f.read()
        f.close()
        
        #
        #key = Fernet.generate_key() #generate key
        #print("Save the key securely. You will need it later.")
        #print("key: \n",key.decode())
        #crypto = Fernet(key)
        
        # Password
        password = getpass("Please enter a passphrase. Store it in a safe place:\n")    # Reads what user inputs
        password=password.encode()
        # print(f'You entered {password} and its type is {type(password)}')     # For testing if format is correct

        
        # Encryption settings
        salt = b'm\xe4\xfb\xaexB\x7f2\xaa\x1dj\x8c\x8f\xf1\\{' # This could be added in a separate file since encryptionHandler needs to use this same value as well
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        crypto = Fernet(key)

        token = crypto.encrypt(blines)
        binfilename = filename.split('.')[0]+".bin"
        f = open(binfilename,"wb") # create binary file
        f.write(token)
        f.close()
        print("created ", binfilename)
    except:
        print("unexpected error occured: ")

if __name__ == "__main__":
    """
    The program can be run by calling: python encryptcredentials.py pth/credentials.txt
    """
    main()