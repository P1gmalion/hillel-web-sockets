import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    active_users = 0

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        ChatConsumer.active_users += 1
        await self.channel_layer.group_send(self.room_group_name,
                                            {"type": "user_count", "connected_users": ChatConsumer.active_users})

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        ChatConsumer.active_users -= 1
        await self.channel_layer.group_send(self.room_group_name,
                                            {"type": "user_count", "connected_users": ChatConsumer.active_users})

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        data = text_data or bytes_data
        text_data_json = json.loads(data)
        message = text_data_json["message"]
        name = text_data_json["name"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message, "name": name}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        name = event["name"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message, "name": name}))

    async def active_users_count(self, event):
        active_users = event["connected_users"]
        await self.send(text_data=json.dumps({"connected_users": active_users}))
