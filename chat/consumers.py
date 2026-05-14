import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import DirectChat, DirectMessage


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        if not self.user.is_authenticated:
            await self.close()
            return

        has_access = await self.user_has_access()
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = (data.get('message') or '').strip()

        if not text:
            return

        message = await self.create_message(text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message['id'],
                'message': message['text'],
                'sender_id': message['sender_id'],
                'sender_name': message['sender_name'],
                'created_at': message['created_at'],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def user_has_access(self):
        try:
            chat = DirectChat.objects.get(pk=self.chat_id)
            return chat.is_participant(self.user)
        except DirectChat.DoesNotExist:
            return False

    @sync_to_async
    def create_message(self, text):
        chat = DirectChat.objects.get(pk=self.chat_id)

        message = DirectMessage.objects.create(
            chat=chat,
            sender=self.user,
            text=text
        )

        chat.set_last_read_message_id_for_user(self.user, message.id)
        chat.save(update_fields=[
            'user1_last_read_message_id',
            'user2_last_read_message_id',
            'updated_at'
        ])

        return {
            'id': message.id,
            'text': message.text,
            'sender_id': self.user.id,
            'sender_name': self.user.get_full_name() or self.user.email,
            'created_at': timezone.localtime(message.created_at).strftime('%d.%m.%Y %H:%M'),
        }