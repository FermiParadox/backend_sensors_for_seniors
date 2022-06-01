# Enable / Disable middlewares
APIKEY_MIDDLEWARE_ACTIVE = True
JWT_MIDDLEWARE_ACTIVE = True

# ------------------------------------------------------------------------------------
JWT_USER_NAME = "backend-SW-Engineer-Candidate"
JWT_TOKEN_DURATION_HOURS = 1
JWT_ALGORITHM = "HS256"

# ------------------------------------------------------------------------------------
#                 EDIT THE SECRETS:
#
# Edit the following if you don't have the IGNORE_GIT_SECRETS file:
API_KEY_VALUE_PAIR = {"x-api-key": "not-actual-value"}
JWT_PRIVATE_KEY = "not-actual-key"

DB_LINK = "not-actual-link"
