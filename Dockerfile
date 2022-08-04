# syntax=docker/dockerfile:1
FROM python:3.10

# to see logs immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /simple_chat
COPY . /simple_chat/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
