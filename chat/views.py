from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView
from rest_framework.views import APIView
from rest_framework import mixins, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import Message, Thread
from .serializers import MessageSerializer, ThreadSerializer, MessageIdListSerializer,\
    UpdatedMessagesAmount, UnreadMessagesAmount, UserIdSerializer


class IsParticipantOfThreadOrAdmin(permissions.IsAuthenticated):
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

    # def has_permission(self, request, view):
    #     return request.user.is_authenticated


class IsMessageReceiverOrAdmin(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        elif type(obj) == Message:
            return request.user != obj.sender and request.user in obj.thread.participants.all()
    #
    # def has_permission(self, request, view):
    #     return request.user.is_authenticated



class ThreadCreateDeleteAPIView(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericAPIView):
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    permission_classes = (IsParticipantOfThreadOrAdmin,)

    def post(self, request, *args, **kwargs):
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
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            if not self.get_object():
                return Response(status=status.HTTP_404_NOT_FOUND)
            return self.destroy(request, *args, **kwargs)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        self.check_object_permissions(self.request, serializer)
        serializer.save()

    def get_object(self):
        try:
            participant1 = self.request.data.get('participants')[0]
            participant2 = self.request.data.get('participants')[1]
            obj = Thread.objects.filter(participants__exact=participant1).get(participants__exact=participant2)
            self.check_object_permissions(self.request, obj)
        except ObjectDoesNotExist:
            return None
        return obj


class ThreadListAPIView(ListAPIView):
    serializer_class = ThreadSerializer
    permission_classes = (permissions.IsAuthenticated,)
    key_name = 'user_id'

    def validate(self):
        if self.key_name not in self.request.GET:
            raise ValidationError({'error': f'param \'{self.key_name}\' must exist'})
        if not User.objects.filter(pk=self.request.GET[self.key_name]).exists():
            raise ValidationError({'error': 'user not found'})

    def get_queryset(self):
        self.validate()
        user = self.request.query_params[self.key_name]
        queryset = Thread.objects.filter(participants=user)

        current_user = self.request.user
        if not current_user.is_staff:
            queryset = queryset.filter(participants=current_user)
        return queryset


class MessageListCreateAPIView(ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = (IsParticipantOfThreadOrAdmin,)
    key_name = 'thread_id'

    def validate(self):
        if self.key_name not in self.request.GET:
            raise ValidationError({'error': f'param \'{self.key_name}\' must exist'})
        if not Thread.objects.filter(pk=self.request.GET[self.key_name]).exists():
            raise ValidationError({'error': 'thread not found'})

    def get_queryset(self):
        self.validate()
        thread_id = self.request.query_params.get(self.key_name)

        thread_obj = Thread.objects.get(id=thread_id)
        self.check_object_permissions(self.request, thread_obj)

        queryset = Message.objects.filter(thread__id=thread_id)

        return queryset

    def perform_create(self, serializer):
        self.check_object_permissions(self.request, serializer)
        serializer.save()


class MessageListMarkIsReadAPIView(APIView):
    serializer_class = MessageIdListSerializer
    permission_classes = (IsMessageReceiverOrAdmin,)

    def put(self, request, *args, **kwargs):
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
    serializer_class = UserIdSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        data = self.request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user_id']
            user_threads = Thread.objects.filter(participants=user)

            queryset = Message.objects
            current_user = self.request.user
            if not current_user.is_staff:
                queryset = queryset.filter(thread__participants=current_user)

            unread_messages_amount = queryset\
                .filter(thread__in=user_threads, is_read=False)\
                .exclude(sender=user.id)\
                .count()
            res_serializer = UnreadMessagesAmount({
                'user_id': user.id,
                'unread_messages_amount': unread_messages_amount})
            return Response(data=res_serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
