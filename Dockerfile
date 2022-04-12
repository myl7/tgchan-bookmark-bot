FROM python:3.10-alpine
WORKDIR /app
COPY LICENSE .
ENV DB_PATH=/db/db.sqlite3
RUN mkdir /db
VOLUME ["/db"]
ENTRYPOINT ["python", "main.py"]
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py schema.sql ./
COPY README.md .
