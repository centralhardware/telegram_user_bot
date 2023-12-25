FROM python:3.8-alpine

WORKDIR /code

COPY requirements.txt .

RUN apk add build-base && \
    pip install -r requirements.txt

COPY src/ .

CMD [ "python", "./main.py" ]
