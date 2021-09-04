# Load secrets
try:
    from app.IGNORE_GIT_SECRETS import PASS_MONGO_DB_USER0, API_KEY_VALUE_PAIR
except ImportError:
    # CHANGE THESE MANUALLY:
    PASS_MONGO_DB_USER0 = "not-actual-password"
    KEY_VALUE_PAIR_PART2 = ("not-actual-key", "not-actual-value")
    # AND REMOVE THE EXCEPTION LINE:
    raise NotImplementedError(
        """The file containing secrets (DB password, api-key, etc.) is not uploaded on Git.
    Please contact me for access or change the values in the code manually.""")
