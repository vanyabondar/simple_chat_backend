from rest_framework import permissions
from .models import Thread, Message
from .serializers import ThreadSerializer, MessageSerializer


class IsParticipantOfThreadOrAdmin(permissions.IsAuthenticated):
    """
    Admin user has permissions for all activities.
    Regular users can get or create thread only if they are participants of this thread.
    Regular users can get message only if they are participants of thread with this message.
    Regular users can create message only if they are sender.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        elif type(obj) == Thread:
            return request.user in obj.participants.all()
        elif type(obj) == Message:
            return request.user in obj.thread.participants.all()
        elif type(obj) == ThreadSerializer:
            return request.user in obj.validated_data['participants']
        elif type(obj) == MessageSerializer:
            return request.user == obj.validated_data['sender']


class IsMessageReceiverOrAdmin(permissions.IsAuthenticated):
    """
    Admin user has permissions for all activities.
    Regular users can create message only if they are receivers of this message.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        elif type(obj) == Message:
            return request.user != obj.sender and request.user in obj.thread.participants.all()


