FROM python:3.12.0-alpine

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY . .
CMD ["python3", "-m" , "migrator"]
