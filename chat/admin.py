from django.contrib import admin

from .models import DirectChat, DirectMessage, DirectMessageAttachment


@admin.register(DirectChat)
class DirectChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'updated_at', 'created_at')
    search_fields = ('user1__email', 'user2__email', 'user1__first_name', 'user2__first_name', 'user1__last_name', 'user2__last_name')
    list_select_related = ('user1', 'user2')


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'created_at')
    search_fields = ('sender__email', 'text')
    list_select_related = ('chat', 'sender')


@admin.register(DirectMessageAttachment)
class DirectMessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'original_name', 'content_type', 'size', 'created_at')
    search_fields = ('original_name', 'content_type', 'message__sender__email')
    list_select_related = ('message',)
