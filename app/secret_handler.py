# Load secrets
try:
    from app.IGNORE_GIT_SECRETS import PASS_MONGO_DB_USER0, API_KEY_VALUE_PAIR, JWT_PRIVATE_KEY

except ImportError:

    from configuration import PASS_MONGO_DB_USER0, API_KEY_VALUE_PAIR, JWT_PRIVATE_KEY
    raise Warning("""Secrets NOT stored on Git (DB password, api-key, etc.). 
    Using default (wrong) values from the configuration file.
    
    Please change the values in the configuration file manually and rerun the code. 
    Also comment out: raise Warning""")
