# To run it
You need MongoDB and you have to edit the DB link in `main.py`. 
Or you can contact me and I will give you access to my DB.

Install all `requirements.txt` and run:   
`$ uvicorn app.main:app --reload`
in the project folder.

You can use Postman for the requests.

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

