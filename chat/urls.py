from django.urls import path
from . import views


urlpatterns = [
    path('api/messages/', views.MessageListCreateAPIView.as_view()),
    path('api/thread/', views.ThreadCreateDeleteAPIView.as_view()),
    path('api/threads/', views.ThreadListAPIView.as_view()),
    path('api/messages/read/', views.MessageListMarkIsReadAPIView.as_view()),
    path('api/messages/unread_amount/', views.UserCountUnreadMessagesAPIView.as_view())
]
