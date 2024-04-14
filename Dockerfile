FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY src/ .

CMD [ "python", "./main.py" ]