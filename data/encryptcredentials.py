import sys
from cryptography.fernet import Fernet

def main(filename = None):
    try:
        if filename is None:
            filename = sys.argv[1]
        # read file contents
        f = open(filename, "rb") #read in binary
        blines = f.read()
        f.close()
        key = Fernet.generate_key() #generate key
        print("Save the key securely. You will need it later.")
        print("key: \n",key.decode())
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