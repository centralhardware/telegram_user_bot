FROM python:3.8

WORKDIR /code

COPY requirements.txt .

RUN apt-get update
RUN apt-get install python-numpy libicu-dev
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt

COPY src/ .

CMD [ "python", "./main.py" ]
