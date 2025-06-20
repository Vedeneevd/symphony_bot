from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database.session import Base


class ChannelPost(Base):
    __tablename__ = 'channel_posts'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, unique=True)  # ID сообщения в Telegram
    text = Column(Text)  # Текст поста
    date = Column(DateTime(timezone=True))  # Дата публикации
    hashtags = Column(String(500))  # Хештеги через запятую
    media_type = Column(String(50))  # 'photo', 'video', 'document'
    media_path = Column(String(500))  # Путь к файлу на диске


class HashtagStats(Base):
    __tablename__ = 'hashtag_stats'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # Фиксированные хештеги
    click_count = Column(Integer, default=0)