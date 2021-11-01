# To run it
You need: 
- Python 
- MongoDB (or contact me and I'll give you access to my DB)
- edit the `configuration.py` to set the correct password values.


Install all `requirements.txt` and run:   
`$ uvicorn app.main:app --reload`
in the project folder.

You can use Postman for the requests. Here are my tests:
[![Run in Postman](https://run.pstmn.io/button.svg)](https://god.gw.postman.com/run-collection/17280509-661ecbc4-1f43-42b5-bf16-778620702e6a?action=collection%2Ffork&collection-url=entityId%3D17280509-661ecbc4-1f43-42b5-bf16-778620702e6a%26entityType%3Dcollection%26workspaceId%3D3add7133-82b3-4bd0-a78c-9647b717d65d)


### Secrets (passwords, api-keys, etc.) not stored on Git
File with secrets is ignored on commits. 


# Middlewares
Api-key middleware and JWT middleware cover endpoints 1-5.

Both middlewares are active by default. 
They can be disabled in `configuration.py`. 

# Endpoints
![image](https://user-images.githubusercontent.com/10809024/132179743-24a93e4b-8f9b-4aa7-8aac-e08dcd808de9.png)


# Testing
Everything has been tested manually with Postman 
and unit-tests, although the latter could 
have been more thorough.


# Race conditions

Some functions are prone to race-conditions when eg.: 
- 2 nurses assign same sensor
- or 1 nurse assigns while other changes table
I should have update conditions checked by MongoDB itself.
