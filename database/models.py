from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.session import Base


class ChannelPost(Base):
    __tablename__ = 'channel_posts'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, unique=True)
    media_group_id = Column(String)  # Для группировки медиа в альбомы
    text = Column(Text)
    date = Column(DateTime(timezone=True), server_default=func.now())
    hashtags = Column(String)

    # Связь с медиафайлами
    media_files = relationship("PostMedia", back_populates="post", cascade="all, delete-orphan")


class PostMedia(Base):
    __tablename__ = 'post_media'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('channel_posts.id'))
    post = relationship("ChannelPost", back_populates="media_files")

    media_type = Column(String)  # photo, video, document, audio и т.д.
    file_id = Column(String)
    file_unique_id = Column(String)
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)  # Для фото/видео
    height = Column(Integer, nullable=True)  # Для фото/видео
    duration = Column(Integer, nullable=True)  # Для видео/аудио
    mime_type = Column(String, nullable=True)  # Для документов
    file_name = Column(String, nullable=True)  # Для документов
    thumbnail_id = Column(String, nullable=True)  # file_id превью
    order_index = Column(Integer)  # Порядок в альбоме


class HashtagStats(Base):
    __tablename__ = 'hashtag_stats'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    click_count = Column(Integer, default=0)