from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.views import APIView
from rest_framework import mixins, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import Message, Thread
from .permissions import IsMessageReceiverOrAdmin, IsParticipantOfThreadOrAdmin
from .serializers import MessageSerializer, ThreadSerializer, MessageIdListSerializer,\
    UpdatedMessagesAmount, UnreadMessagesAmount, UserIdSerializer


class ThreadCreateDeleteAPIView(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericAPIView):
    """
    APIView allows to create/delete or retrieve (if thread with the same users exists) Thread.
    """
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    permission_classes = (IsParticipantOfThreadOrAdmin,)

    def post(self, request, *args, **kwargs):
        """
        If request data is not valid, returns HTTP_400_BAD_REQUEST.
        If thread exists, returns thread and HTTP_200_OK
        If thread does not exist, create and returns thread and HTTP_201_CREATED
        """
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            obj = self.get_object()
            if not obj:
                return self.create(request, *args, **kwargs)
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        If request data is not valid, returns HTTP_400_BAD_REQUEST
        If thread does not exist, returns HTTP_404_NOT_FOUND
        If thread exists, deletes thread and returns HTTP_204_NO_CONTENT
        """
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            if not self.get_object():
                return Response(status=status.HTTP_404_NOT_FOUND)
            return self.destroy(request, *args, **kwargs)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # redefinition perform_create method to check if user has permission on creating object
    def perform_create(self, serializer):
        self.check_object_permissions(self.request, serializer)
        serializer.save()

    def get_object(self):
        try:
            # try to find thread that have both of participants
            participant1 = self.request.data.get('participants')[0]
            participant2 = self.request.data.get('participants')[1]
            obj = Thread.objects.filter(participants__exact=participant1).get(participants__exact=participant2)
            self.check_object_permissions(self.request, obj)
        except ObjectDoesNotExist:
            return None
        return obj


class ThreadListAPIView(ListAPIView):
    """
    APIView allows to get list of thread for user (every thread has last message).
    """
    serializer_class = ThreadSerializer
    permission_classes = (permissions.IsAuthenticated,)
    key_name = 'user_id'

    def validate(self):
        """
        Validates that param 'user_id' exists in GET params and user with this id exists.
        """
        if self.key_name not in self.request.query_params:
            raise ValidationError({'error': f'param \'{self.key_name}\' must exist'})
        if not User.objects.filter(pk=self.request.query_params[self.key_name]).exists():
            raise ValidationError({'error': 'user not found'})

    def get_queryset(self):
        """
        For admin gets queryset with all threads when user is participant.
        For regular users gets queryset with threads when current user is participant.
        """
        self.validate()
        user = self.request.query_params[self.key_name]
        queryset = Thread.objects.filter(participants=user)

        current_user = self.request.user
        if not current_user.is_staff:
            queryset = queryset.filter(participants=current_user)
        return queryset


class MessageListCreateAPIView(ListCreateAPIView):
    """
    APIView allows to create message or get list of messages for thread.
    """
    serializer_class = MessageSerializer
    permission_classes = (IsParticipantOfThreadOrAdmin,)
    key_name = 'thread_id'

    def validate(self):
        """
        Validates that param 'thread_id' exists in GET params and thread with this id exists.
        """
        if self.key_name not in self.request.query_params:
            raise ValidationError({'error': f'param \'{self.key_name}\' must exist'})
        if not Thread.objects.filter(pk=self.request.query_params[self.key_name]).exists():
            raise ValidationError({'error': 'thread not found'})

    def get_queryset(self):
        """
        Gets queryset with messages from the given thread.
        Check permissions current user on this thread.
        """
        self.validate()
        thread_id = self.request.query_params.get(self.key_name)

        thread_obj = Thread.objects.get(id=thread_id)
        self.check_object_permissions(self.request, thread_obj)

        queryset = Message.objects.filter(thread__id=thread_id)

        return queryset

    # redefinition perform_create method to check if user has permission on creating object
    def perform_create(self, serializer):
        self.check_object_permissions(self.request, serializer)
        serializer.save()


class MessageListMarkIsReadAPIView(APIView):
    """
    APIView allows to mark that messages from list messages have already been read
    """
    serializer_class = MessageIdListSerializer
    permission_classes = (IsMessageReceiverOrAdmin,)

    def put(self, request, *args, **kwargs):
        """
        If request data is not valid, returns HTTP_400_BAD_REQUEST.
        Checks that current user has permissions on updating this messages.
        If request data is valid and user has permissions, updates messages returns messages and HTTP_200_OK
        """
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            messages_queryset = Message.objects.filter(id__in=serializer.validated_data['message_ids'])
            for message in messages_queryset.all():
                self.check_object_permissions(self.request, message)
            updated_amount = messages_queryset.update(is_read=True)
            res_serializer = UpdatedMessagesAmount({'updated_messages_amount': updated_amount})
            return Response(res_serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCountUnreadMessagesAPIView(APIView):
    """
    APIView allows to get amount of unread messages for user
    """
    serializer_class = UserIdSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
        If request data is not valid, returns HTTP_400_BAD_REQUEST.
        Returns user_id and amount of unread messages for this user and HTTP_200_OK.
        """
        data = self.request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user_id']

            queryset = self.get_queryset(user)
            unread_messages_amount = queryset.count()

            res_serializer = UnreadMessagesAmount({
                'user_id': user.id,
                'unread_messages_amount': unread_messages_amount})
            return Response(data=res_serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, user):
        """
        For admin gets full queryset of unread messages for the given user.
        For regular user gets queryset of unread messages only for thread when current user is participant
        """
        queryset = Message.objects
        current_user = self.request.user
        if not current_user.is_staff:
            queryset = queryset.filter(thread__participants=current_user)

        user_threads = Thread.objects.filter(participants=user)
        queryset = queryset \
            .filter(thread__in=user_threads, is_read=False) \
            .exclude(sender=user.id)

        return queryset
