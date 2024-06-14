FROM python:3.12.3-alpine3.18

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY . .
CMD ["python3", "main.py"]
