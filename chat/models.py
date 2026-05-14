from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now
from pathlib import Path
from django.db.models.signals import post_delete
from django.dispatch import receiver

if TYPE_CHECKING:
    from users.models import User


class DirectChat(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_chats_as_user1',
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direct_chats_as_user2',
    )
    user1_last_read_message_id = models.PositiveBigIntegerField(null=True, blank=True)
    user2_last_read_message_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['user1', 'user2'], name='unique_direct_chat_users'),
            models.CheckConstraint(check=~Q(user1=F('user2')), name='direct_chat_no_self'),
        ]

    @classmethod
    def get_or_create_for_users(cls, a: 'User', b: 'User') -> 'DirectChat':
        if a.pk is None or b.pk is None:
            raise ValueError('Both users must be saved before creating a chat.')
        if a.pk == b.pk:
            raise ValueError('Cannot create a direct chat with self.')
        user1, user2 = (a, b) if a.pk < b.pk else (b, a)
        chat, _created = cls.objects.get_or_create(user1=user1, user2=user2)
        return chat

    def other_user(self, user: 'User') -> 'User':
        if user.pk == self.user1_id:
            return self.user2
        return self.user1

    def is_participant(self, user: 'User') -> bool:
        return user.pk in {self.user1_id, self.user2_id}

    def last_read_message_id_for_user(self, user: 'User') -> int | None:
        if user.pk == self.user1_id:
            return self.user1_last_read_message_id
        if user.pk == self.user2_id:
            return self.user2_last_read_message_id
        return None

    def set_last_read_message_id_for_user(self, user: 'User', message_id: int | None) -> None:
        if user.pk == self.user1_id:
            self.user1_last_read_message_id = message_id
        elif user.pk == self.user2_id:
            self.user2_last_read_message_id = message_id

    def __str__(self) -> str:
        return f'Chat {self.user1_id}↔{self.user2_id}'


class DirectMessage(models.Model):
    chat = models.ForeignKey(DirectChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='direct_messages_sent')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            DirectChat.objects.filter(pk=self.chat_id).update(updated_at=Now())

    def __str__(self) -> str:
        return f'Message {self.pk} in chat {self.chat_id}'


class DirectMessageAttachment(models.Model):
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            name = getattr(self.file, 'name', '') or ''
            self.original_name = Path(name).name or self.original_name
        if self.file:
            ct = getattr(getattr(self.file, 'file', None), 'content_type', '') or ''
            if ct and not self.content_type:
                self.content_type = ct
            try:
                self.size = int(getattr(self.file, 'size', 0) or 0)
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def is_image(self) -> bool:
        return (self.content_type or '').startswith('image/')

    def __str__(self) -> str:
        return self.original_name or f'Attachment {self.pk}'


@receiver(post_delete, sender=DirectMessageAttachment)
def _delete_attachment_file(sender, instance: DirectMessageAttachment, **kwargs):
    try:
        if instance.file:
            instance.file.delete(save=False)
    except Exception:
        pass
