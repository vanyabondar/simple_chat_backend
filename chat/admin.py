from django.contrib import admin
from django.contrib.auth.models import User
from .models import Message, Thread
from .forms import ThreadForm


class AdminUser(admin.ModelAdmin):
    list_display = ['id', 'username']


class AdminThread(admin.ModelAdmin):
    list_display = ['id', '__str__', 'created', 'updated']
    form = ThreadForm


class AdminMessage(admin.ModelAdmin):
    list_display = ['id', 'thread', 'sender', 'text', 'created']


admin.site.register(Message, AdminMessage)
admin.site.register(Thread, AdminThread)

admin.site.unregister(User)
admin.site.register(User, AdminUser)