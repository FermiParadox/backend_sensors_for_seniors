# REST API toy project
Αllows registering seniors, clinics, sensors. Endpoints are protected with JWT and/or an API-key.

![image](https://user-images.githubusercontent.com/10809024/132179743-24a93e4b-8f9b-4aa7-8aac-e08dcd808de9.png)

# To run it
You need: 
- Python 
- MongoDB 
- edit the `configuration.py` to set the correct password values.


Install all `requirements.txt` and run:   
`$ uvicorn app.main:app --reload`
in the project folder.


### Secrets (passwords, api-keys, etc.) not stored on Git
File with secrets is ignored on commits. (PS: I should have used env-variables)


# Middlewares
Api-key middleware and JWT middleware cover endpoints 1-5.

Both middlewares are active by default. 
They can be disabled in `configuration.py`. 


# Testing
Everything has been tested manually with Postman 
and unit-tests, although the latter could 
have been more thorough (and less complicated).


# Issues
Some functions are prone to race-conditions when e.g.: 
- 2 nurses assign same sensor
- or 1 nurse assigns while other changes table
I should have update-conditions checked by MongoDB itself.
