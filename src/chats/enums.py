import enum

class ERR(str, enum.Enum):
    INVALID_ACTION = "INVALID_ACTION"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    SERVER_ERROR = "SERVER_ERROR"
    MODULE_NOT_FOUND = "MODULE_NOT_FOUND"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    INVALID_JSON = "INVALID_JSON"
    INTERNAL_ERROR = "INTERNAL_ERROR"

ErrorTypes = ERR


class BroadCastAction(str, enum.Enum):
    GROUP_TYPING = "group.typing"
    GROUP_CREATED = "group.created"
    GROUP_READ_RECIEPT = "group.read_receipt"
    SEND_MESSAGE = "send.message"
    PRESENCE_USER_ONLINE = "presence.user_online"
    PRESENCE_USER_OFFLINE = "presence.user_offline"