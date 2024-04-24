from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from api.models import Chat, Inbox
from api.serializer import chatSerializer
from api.custom_auth import websocket_auth
from rest_framework.exceptions import AuthenticationFailed

class chatConsumer(AsyncJsonWebsocketConsumer):


    @database_sync_to_async
    def update_chat_seen(self, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            chat.seen = True
            chat.save()
        except Exception as e:
            print(e)

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            user, error = websocket_auth(token=token)
            if not error is None:
                return
            return str(user.id)
        except Exception as e:
            raise AuthenticationFailed("Invalid token")

    @database_sync_to_async
    def save_message(self, content):
        try:
            data = {
                "inbox": self.room_group_name,
                "sender": content.get("sender", None),
                "message": content.get("message", None)
            }
            serializer = chatSerializer(data=data)
            if not serializer.is_valid():
                print(serializer.errors, self.room_group_name)
                return False
            serializer.save()
            inbox = Inbox.objects.get(id=self.room_group_name)
            inbox.last_message = data['message']
            inbox.save()
            return serializer.data
        except Exception as e:
            print(e)
            return None
        

    async def connect(self):
        self.room_group_name = None
        await self.accept()
    
    async def receive_json(self, content, **kwargs):
        message_type = content['type']

        if message_type == 'message':
            saved = await self.save_message(content)
            if not saved:
                return await self.send_json({"type": "error", "message": "Unable to save message"})
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_message",
                    "data": {
                        "message": content['message'],
                        "sender": content['sender'],
                        "id": saved['id'],
                        "receiver": content['receiver']
                    },
                }
            )
            await self.channel_layer.group_send(
                content['receiver'],
                {
                    "type": "send_message",
                    "data": {
                        "type": "notification",
                        "inbox": self.room_group_name,
                        "message": content['message']
                    }
                }
            )
        elif message_type == 'join_room':
            if self.room_group_name:
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            self.room_group_name = content['room']
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        elif message_type == 'auth':
            token = content['token']
            try:
                userId = await self.get_user_from_token(token)
                await self.channel_layer.group_add(userId, self.channel_name)
            except Exception as e:
                print(e)
                await self.disconnect()
        elif message_type == 'msg_seen':
            msg_id = content['id']
            try:
                await self.update_chat_seen(msg_id)
            except Exception as e:
                print(e)
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print("1 user disconnected!")
    
    async def send_message(self, event):
        await self.send_json(event['data'])
