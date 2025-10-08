FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential binutils \
 && pip install --no-compile --disable-pip-version-check -r requirements.txt \
 # подчистим статические либы/кэш/байткод
 && find /usr/local -type f -name '*.a' -delete || true \
 && find /usr/local -type d -name '__pycache__' -exec rm -rf {} + || true \
 && find /usr/local -type f -name '*.py[co]' -delete || true \
 # уменьшим .so (безопасно для python-расширений)
 && find /usr/local -type f -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
 # удаляем компилятор и зависимости, чистим списки пакетов
 && apt-get purge -y --auto-remove build-essential binutils \
 && rm -rf /var/lib/apt/lists/*



COPY src/ .

CMD [ "python", "./main.py" ]
