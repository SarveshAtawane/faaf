import os

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://sarveshatawane03:y2flIDD1EmOaU5de@cluster0.sssmr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME: str = os.getenv("DB_NAME", "chat_app")
    ALLOWED_ORIGINS = ["*"]
    # bcrypt settings
    BCRYPT_ROUNDS: int = 12

settings = Settings()
