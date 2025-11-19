import uuid
from django.db import models


class ChatRoom(models.Model):
    CHAT_TYPES = [
        ("product", "Product Chat"),
        ("dm", "Direct Message"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chatrooms",
    )
    participants = models.ManyToManyField(
        "users.User", through="chats.ChatParticipant", related_name="chatrooms"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chat_type} chat {self.id}"


class ChatParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatroom = models.ForeignKey(
        "chats.ChatRoom", on_delete=models.CASCADE, related_name="participants_info"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="chat_participations"
    )
    has_ordered = models.BooleanField(default=False)
    orders = models.ManyToManyField(
        "orders.Order", blank=True, related_name="chat_participants"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("chatroom", "user")

    def __str__(self):
        return f"{self.user} in {self.chatroom}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatroom = models.ForeignKey(
        "chats.ChatRoom", on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="messages"
    )
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} in {self.chatroom}"


class Reaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        "chats.Message", on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="reactions"
    )
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user")

    def __str__(self):
        return f"{self.user} reacted {self.emoji} on {self.message.id}"


class PinnedMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatroom = models.ForeignKey(
        "chats.ChatRoom", on_delete=models.CASCADE, related_name="pinned_messages"
    )
    message = models.OneToOneField(
        "chats.Message", on_delete=models.CASCADE, related_name="pinned"
    )
    pinned_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="pinned_messages",
    )
    pinned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.message.id} pinned in {self.chatroom}"


class Attachment(models.Model):
    ATTACHMENT_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
        ("audio", "Audio"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        "chats.Message", on_delete=models.CASCADE, related_name="attachments"
    )
    file_url = models.URLField()
    type = models.CharField(max_length=10, choices=ATTACHMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} for {self.message.id}"
