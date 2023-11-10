FROM python:3.11

WORKDIR /app

COPY Josix/ ./

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python3", "josix.py" ]
