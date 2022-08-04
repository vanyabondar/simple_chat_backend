
# Simple chat API

This is REST API for simple chat written in Python3 using Django and DRF.


## Stack
- Python3
- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
- [Dotenv](https://pypi.org/project/python-dotenv/)
- [Docker](https://www.docker.com/)


## Features
App has 2 models: Thread and Message.
 - Create/delete or retrieve (if thread with the same users exists) Thread
 - Get list of thread for user (every thread has last message)
 - Create message or get list of messages for thread
 - Mark that messages from list messages have already been read
 - Get amount of unread messages for user
 - Permissions: 
     - regular users can get/edit information only if they are participants of this thread
     - admin has access to all threads and messages 
 - Pagination
 - Authentication provided by JWT
 - Docker support


## Usage
Action | URL | Method
------------ | ------------- | -------------
Obtain token | /api/auth/token/ | POST
Refresh token | /api/auth/refresh/ | POST
Create/Get/Delete thread | /api/thread/ | POST/DELETE 
Get list of threads for user | /api/threads | GET 
Create or get list of messages | /api/messages/ | POST/GET 
Mark messages as read | /api/messages/read/ | PUT 
Count unread messages for user | /api/messages/unread_amount/ | POST 


## Setup
Clone the repository and change the working directory:

    git clone https://github.com/vanyabondar/simple_chat_backend
    cd simple_chat
Create .env file with your environment variables:

    SECRET_KEY=***** 

### Run from docker image 
Build image from Dockerfile:
    
    sudo docker build -t simple_chat .
Run container

    sudo docker run -p 8000:8000 simple_chat


### Run by python

Create and activate the virtual environment:

    python3 -m venv ./venv
    source ./venv/bin/activate
Install requirements:

    pip3 install -r requirements.txt


Run the server:

    python3 manage.py runserver
   

