# To run it
Install all `requirements.txt` and run:   
`$ uvicorn app.main:app --reload`
in the project folder.

You can use Postman for the requests.
https://www.getpostman.com/collections/d19173f68f3128c4a7a3

### Middlewares
Api-key middleware covers all endpoints.
JWT middleware covers all except token provider 
endpoint.

Both middlewares are active by default. 
They can be disabled in `configuration.py`. 



### Secrets not stored on Git
File with secrets is ignored on commits.   
Please edit `configuration.py` to set the correct 
passwords.

### Testing
Everything has been tested manually 
and through unit-tests, although the latter could 
have been more thorough. 

The unit-tests work when JWT-middleware is disabled.
I can make them work with it as well if needed.


### Race conditions

Some functions are prone to race-conditions when eg.: 
- 2 nurses assign same sensor
- or 1 nurse assigns while other changes table

