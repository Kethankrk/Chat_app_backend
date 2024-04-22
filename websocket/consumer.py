from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from api.models import Chat, Inbox
from api.serializer import chatSerializer

class chatConsumer(AsyncJsonWebsocketConsumer):

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
                print(serializer.errors)
                return False
            serializer.save()
            inbox = Inbox.objects.get(id=self.room_group_name)
            inbox.last_message = data['message']
            inbox.save()
            return True
        except Exception as e:
            print(e)
            return False
        

    async def connect(self):
        self.room_group_name = self.scope['url_route']['kwargs']['inbox_id']
        if self.room_group_name:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.disconnect()
    
    async def receive_json(self, content, **kwargs):
        print(self.room_group_name)
        saved = await self.save_message(content)
        if not saved:
            return self.send_json({"type": "error", "message": "Unable to save message"})
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_message",
                "data": {
                    "message": content['message'],
                    "sender": content['sender']
                },
            }
        )
    
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print("1 user disconnected!")
    
    async def send_message(self, event):
        await self.send_json(event['data'])