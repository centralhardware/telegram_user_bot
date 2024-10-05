FROM python

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .

RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:80/health || exit 1


CMD [ "python", "./main.py" ]