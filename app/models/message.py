from pydantic import BaseModel, Field

class MessageCreate(BaseModel):
    senderId: str = Field(...)
    receiverId: str = Field(...)
    message: str = Field(...)

class MessageOut(BaseModel):
    id: str
    senderId: str
    senderEmail: str
    senderName: str
    receiverId: str
    receiverEmail: str
    receiverName: str
    message: str
    timestamp: str
