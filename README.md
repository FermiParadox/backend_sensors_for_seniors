# To run it
You need Python, MongoDB and you have to edit the DB link in `main.py`. 
Or you can contact me and I will give you access to my DB.

Install all `requirements.txt` and run:   
`$ uvicorn app.main:app --reload`
in the project folder.

You can use Postman for the requests.


### Secrets (passwords, api-keys, etc.) not stored on Git
File with secrets is ignored on commits.   
Please edit `configuration.py` to set the correct values.


### Middlewares
Api-key middleware and JWT middleware cover endpoints 1-5.

Both middlewares are active by default. 
They can be disabled in `configuration.py`. 

### Endpoints
![image](https://user-images.githubusercontent.com/10809024/132179743-24a93e4b-8f9b-4aa7-8aac-e08dcd808de9.png)


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

### Async mongoDB
It hasn't been implemented. I can do so if needed.

