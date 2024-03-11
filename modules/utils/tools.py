import random
import string
import time

def generate_random_string(length=10):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

def generate_external_ref():
    timestamp = int(time.time())
    return "BILLY_" + generate_random_string(7) +  str(timestamp)