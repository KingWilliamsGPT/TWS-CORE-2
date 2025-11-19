# consumers.py
import json
import logging
import sys
import enum
import asyncio
from typing import Dict, Any, Optional

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone

from src.users.models import User
from src.chats.models import (
    ChatParticipant,
    ChatRoom,
    Message,
    PinnedMessage,
    Attachment,
    Reaction,
)


from .enums import ERR, BroadCastAction

logger = logging.getLogger(__name__)



SEND_PING_INTERVAL = 30  # seconds


class GroupManagerMixin:
    # Mixin class for my AppConsumer(AsyncWebsocketConsumer)
    # Django automatically removes 

    async def join_broadcast_group(self, group_name: str):
        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )

    async def leave_broadcast_group(self, group_name: str):
        await self.channel_layer.group_discard(
            group_name,
            self.channel_name
        )

    async def send_group(self, group_name: str, payload: Dict[str, Any], broadcast_action: BroadCastAction):
        """
        Sends a broadcast event to all members of a group.
        """

        user = getattr(self, "user", None) or getattr(self, "_user", None)

        data = {
            "broadcast": True,
            "action": broadcast_action.value,
            "payload": payload,
            "timestamp": timezone.now().isoformat(),
            "sender": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_name(),
                "picture_url": user.picture_url,
            } if user else None,
        }

        await self.channel_layer.group_send(
            group_name,
            {
                "type": "group_broadcast_dispatch",
                "data": data,
            }
        )

    async def group_broadcast_dispatch(self, event: Dict[str, Any]):
        """
        One universal handler for all group events.
        Send's messages to my client/browser/app
        """
        await self.send_json(event["data"])



class AppConsumer(GroupManagerMixin, AsyncWebsocketConsumer):
    """Main WebSocket consumer with modular action handling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modules = {}
        self.ping_task = None
        self.user = None
        self.db_services = DatabaseServices(consumer=self)
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Import modules here to avoid circular imports
        from .consumer_modules import (
            GroupChatModule,
            DirectChatModule,
            PresenceModule,
            NotificationModule,
            CallModule,
            MediaModule,
            ContactModule,
            StoryModule,
            SyncModule,
            SettingsModule,
            EncryptionModule,
        )
        # Authentication check
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            print("WS: Connection rejected: Unauthenticated user", file=sys.stderr)
            await self.close(code=4001)
            return
        
        await self.accept()
        logger.info(f"User {self.user.id} connected")

        self.db_services.user = self.user
        
        # Initialize all modules
        self.modules = {
            'GROUP_CHAT': GroupChatModule(self),
            'DIRECT_CHAT': DirectChatModule(self),
            'PRESENCE': PresenceModule(self),
            'NOTIFICATION': NotificationModule(self),
            'CALL': CallModule(self),
            'MEDIA': MediaModule(self),
            'CONTACT': ContactModule(self),
            'STORY': StoryModule(self),
            'SYNC': SyncModule(self),
            'SETTINGS': SettingsModule(self),
            'ENCRYPTION': EncryptionModule(self),
        }
        
        # Join user's personal channel (for multi-device sync)
        await self.join_broadcast_group(f"user_{self.user.id}")
        
        # for module in self.modules.values():
        #     if hasattr(module, 'on_connect'):
        #         await module.on_connect() # eg. await self.modules['PRESENCE'].handle_user_online()
        await asyncio.gather(
            *(m.on_connect() for m in self.modules.values() if hasattr(m, "on_connect"))
        )

        # Start heartbeat
        self.ping_task = asyncio.create_task(self.ping_loop())
        
        # Send connection confirmation
        await self.send_json({
            "type": "connected",
            "user_id": self.user.id,
            "timestamp": timezone.now().isoformat()
        })
        
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if not self.user or not self.user.is_authenticated:
            return
        
        # Stop heartbeat
        if self.ping_task:
            self.ping_task.cancel()
        
        # for module in self.modules.values():
        #     if hasattr(module, 'on_disconnect'):
        #         await module.on_disconnect() # eg. await self.modules['PRESENCE'].handle_user_offline()
        await asyncio.gather(
            *(m.on_disconnect() for m in self.modules.values() if hasattr(m, "on_disconnect"))
        )

        # Leave user's personal channel
        await self.leave_broadcast_group(f"user_{self.user.id}")
        
        # Leave all group channels
        await self.leave_user_groups()
        
        logger.info(f"User {self.user.id} disconnected (code: {close_code})")

    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        # actions format MY_ACTION
        try:
            if not text_data:
                return
            
            data = json.loads(text_data)
            action = data.get('action')
            payload = data.get('payload', {})
            
            # Handle heartbeat pong
            if action == 'pong':
                await asyncio.gather(
                    *(m.on_pong() for m in self.modules.values() if hasattr(m, "on_pong"))
                )
                return
            
            action = action.upper()

            # Parse action format: WS:MODULE:ACTION
            if not action or not action.startswith('WS:'):
                await self.send_error("Invalid action format", ERR.INVALID_ACTION)
                return
            
            parts = action.split(':')
            if len(parts) < 3:
                await self.send_error("Invalid action format", ERR.INVALID_ACTION)
                return
            
            module_name = parts[1].strip().lower() # MODULE
            action_name = parts[2].strip().lower() # ACTION
            
            # Get module
            module = self.modules.get(module_name)

            if not module:
                await self.send_error(f"Module '{module_name}' not found", ERR.MODULE_NOT_FOUND)
                return
            

            # Get action handler
            handler_name = f"ACTION_{action_name}"
            handler = getattr(module, handler_name, None)
            
            if not handler or not callable(handler):
                await self.send_error(f"Action '{action_name}' not found in module '{module_name}'", ERR.ACTION_NOT_FOUND)
                return
            
            # Execute action
            module._current_action = action 
            await handler(payload=payload)
            
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format", ERR.INVALID_JSON)
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            await self.send_error("Internal server error", ERR.INTERNAL_ERROR)
    

    async def ping_loop(self):
        """Heartbeat loop to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(SEND_PING_INTERVAL)  # Send ping every 30 seconds
                await self.send_json({"type": "ping"})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping loop error: {str(e)}")
    
    




class AutoDBMeta(type):
    """Metaclass to auto-wrap db_ methods with database_sync_to_async.
    
    Similar to doing this manually:
    ```
    >>> class Service:
            @database_sync_to_async
            def db_method(self, *args, **kwargs):
                ...
    ```

    MAKE SURE NOT TO MAKE THE METHOD ASYNC, as database_sync_to_async
    expects a synchronous function to wrap.
    DONOT DO THIS
    ```
    >>> class Service(metaclass=AutoDBMeta):
            async def db_method(self, *args, **kwargs):  # WRONG
                ...
    ```

    Also note that the db_* methods should be awaited
    ```
    >>> service = Service()
    >>> result = await service.db_method(args)
    ```
    """
    def __new__(cls, name, bases, attrs):
        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and (attr_name.startswith("db_") or attr_name.startswith("redis_")):
                # wrap it if not already wrapped
                method = database_sync_to_async(attr_value)
                attrs[attr_name] = method
        return super().__new__(cls, name, bases, attrs)


class GroupWebsocketServiceMixin:
    def db_fetch_groups_for_user(self):
        """Fetch all groups for a user from the database."""
        return ChatRoom.objects.filter(participants__id=self.user.id).distinct()


class PresenceWebsocketServiceMixin:
    def redis_i_am_onine(self):
        """Mark user as online in Redis."""
        cache.set(f"user_online_{self.user.id}", True, timeout=300)  # 5 minutes
    
    def redis_i_am_offline(self):
        """Mark user as offline in Redis."""
        cache.delete(f"user_online_{self.user.id}")
    
    def redis_is_user_online(self, user_id: int) -> bool:
        """Check if a user is online in Redis."""
        return cache.get(f"user_online_{user_id}") is True
    
    def redis_refresh_online_status(self):
        """Refresh the online status timeout for the user."""
        cache.set(f"user_online_{self.user.id}", True, timeout=300)  # 5 minutes

    

class DatabaseServices(
        GroupWebsocketServiceMixin, 
        metaclass=AutoDBMeta
    ):
    """Service class with auto-wrapped db_ methods."""
    def __init__(self, consumer: AppConsumer):
        self.consumer = consumer
        self.user = None