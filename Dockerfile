# syntax=docker/dockerfile:1
FROM python:3.8
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
COPY ./app /code/app
COPY configuration.py configuration.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]