from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.session import Base


class ChannelPost(Base):
    __tablename__ = 'channel_posts'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, unique=True)
    text = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())
    hashtags = Column(String)  # Сохраняем хештеги как строку через запятую


class HashtagStats(Base):
    __tablename__ = 'hashtag_stats'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # Фиксированные хештеги
    click_count = Column(Integer, default=0)