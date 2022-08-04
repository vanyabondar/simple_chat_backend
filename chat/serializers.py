from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Message, Thread


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

    def validate(self, attrs):
        """
        Check that sender is participant of this thread
        """
        participants = User.objects.filter(thread=attrs['thread'])
        if attrs['sender'] not in participants:
            raise serializers.ValidationError("Sender is not participant of this thread")
        return attrs


class ThreadSerializer(serializers.ModelSerializer):
    last_message = MessageSerializer(read_only=True)

    def validate(self, attrs):
        """
        Check that thread has exactly 2 different participants
        """
        participants = attrs['participants']
        if len(participants) != 2 or participants[0] == participants[1]:
            raise serializers.ValidationError("Thread must include exactly 2 different participants")

        return attrs

    class Meta:
        model = Thread
        fields = ['id', 'participants', 'created', 'updated', 'last_message']


class MessageIdListSerializer(serializers.Serializer):
    message_ids = serializers.ListField(child=serializers.IntegerField())

    def validate(self, attrs):
        """
        Check that all messages exist
        """
        message_id_list = attrs['message_ids']
        existing_messages_amount = Message.objects.filter(id__in=message_id_list).count()
        if existing_messages_amount != len(message_id_list):
            raise serializers.ValidationError("Not all messages exist")
        return attrs


# Serializers for response
class UserIdSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class UpdatedMessagesAmount(serializers.Serializer):
    updated_messages_amount = serializers.IntegerField()


class UnreadMessagesAmount(serializers.Serializer):
    user_id = serializers.IntegerField()
    unread_messages_amount = serializers.IntegerField()
