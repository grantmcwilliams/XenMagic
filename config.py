import os 
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

home_dir = os.path.dirname(__file__)
users = {"admin": "0fce9a780dcffb9a75c7e723cdd6b1b1"}
def encrypt_password(passwd):
    m = md5.new()
    m.update(passwd)
    return m.hexdigest()
