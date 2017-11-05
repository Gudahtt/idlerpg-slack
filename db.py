import os
import pickle

def save(filename, data):
    """Save the current user information to disk

    A clone is created of the user copy before saving, so that all users
    can be set to offline before being saved to disk
    """
    with open(filename, 'wb') as db_file:
        pickle.dump(data, db_file, protocol=pickle.HIGHEST_PROTOCOL)

def load(filename):
    """Load user information from disk"""
    if os.path.isfile(filename):
        with open(filename, 'rb') as db_file:
            return pickle.load(db_file)
