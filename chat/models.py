from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Thread(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    participants = models.ManyToManyField(User, related_name='thread')

    def last_message(self):
        try:
            message = Message.objects.filter(thread=self.id).latest('created')
        except ObjectDoesNotExist:
            message = None
        return message

    def __str__(self):
        return ' '.join([user.username for user in self.participants.all()])


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_query_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'[{str(self.thread)}] {self.sender.username}: \"{self.text}\"'
