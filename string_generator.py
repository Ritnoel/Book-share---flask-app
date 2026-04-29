import random


def random_string():
    string = "qwertyuiopasdfghjklzxcvbnm"
    name = ""
    for _ in range(30):
        name += random.choice(string)
    
    return name
