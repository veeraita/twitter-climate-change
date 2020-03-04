import base64
import os
from getpass import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Password
password = getpass("Please enter the passphrase for decryption:\n")    # Reads what user inputs
password=password.encode() # Exception handler needs to be added for wrong passwords

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
f = Fernet(key)




# Encode the message
#message='deep dark secret'
#encodedMessage=message.encode()

# Encrypt the message
#encrypted = f.encrypt(encodedMessage)
#file=open('EncodedCulo.txt','wb') # Write in Binary mode
#file.write(encrypted)
#file.close()

# Open the encrypted file
encryptedFile=open('culoCredentials.bin','rb')
encryptedMessage=encryptedFile.read()
encryptedFile.close()

# Decrypt the encrypted message
decryptedMessage=f.decrypt(encryptedMessage)
print(decryptedMessage.decode())

