# Load secrets
try:
    from app.IGNORE_GIT_SECRETS import PASS_MONGO_DB_USER0, API_KEY_VALUE_PAIR, JWT_PRIVATE_KEY

except ImportError:

    from configuration import PASS_MONGO_DB_USER0, API_KEY_VALUE_PAIR, JWT_PRIVATE_KEY
    print("""WARNING: Secrets NOT stored on Git (DB password, api-key, etc.). 
    Using default (wrong) values from configuration file.
    
    Please change edit configuration file manually. 
    If already done, ignore this message.""")
