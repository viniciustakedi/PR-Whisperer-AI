import os

def getEnv(name):
    envValue = os.getenv(name)
    if not envValue:
        raise Exception(f"{name} is not set")
    return envValue