from django.urls import path

from .views import delete_direct_message_view, direct_chat_thread_view, inbox_view, start_direct_chat_view

urlpatterns = [
    path('', inbox_view, name='chat_inbox'),
    path('start/<int:user_id>/', start_direct_chat_view, name='chat_start'),
    path('<int:chat_id>/', direct_chat_thread_view, name='chat_thread'),
    path('<int:chat_id>/delete/<int:message_id>/', delete_direct_message_view, name='chat_message_delete'),
]
