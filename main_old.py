from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func, DateTime, Date
from sqlalchemy.orm import sessionmaker, declarative_base,relationship
Base = declarative_base()
engine = create_engine('sqlite:///demo.db')

Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)
    phone = Column(String)
    birthday = Column(Date)

def get_id(user_id):
    user = session.query(User).filter(User.id == user_id).first()
    return user.id if user else None

def get_name(user_id):
    user = session.query(User).filter(User.id == user_id).first()
    return user.name if user else None

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    price = Column(Integer)

def get_product_id(self,product_name:str):
    product = self.session.query(Product).filter(Product.name == product_name).first()
    return product if product else None

# def get  # исходный файл содержал незавершённую функцию

# class TikTokUser(Base):
#     __tablename__ = 'tiktok_user'
#     id = Column(Integer, primary_key=True)
#     username = Column(String)
#     subscribers = Column(Integer, default=0)
#     videos = relationship("Video", back_populates="author_id")
#
# class Video(Base):
#     __tablename__ = 'tiktok_video'
#     id = Column(Integer, primary_key=True)
#     title = Column(String)
#     views = Column(String, default=0)
#     creator_id = Column(Integer, ForeignKey('tiktok_user.id'))
#     author_id = relationship("TikTokUser", back_populates="videos")
#
# Base.metadata.create_all(engine)
#
# vluud = TikTokUser(username="vluud")
# video1 = Video(title="video1")
# video2 = Video(title="video2")
# vluud.videos = [video1, video2]
# session.add(vluud)
# session.commit()
#
# user = session.query(TikTokUser).all()
# for user in user:
#     print(f'Юзернейм:{user.username}')
#     print("Видео:")
#     for videos in user.videos:
#         print(f'-- {videos.title}')

# # maria = User(name='maria', age=18)
# # oleg = User(name='oleg', age=21)
# # session.add_all([maria, oleg])
# # session.commit()
#
# users = session.query(func.max(User.id)).count()
# print(users)
# # for user in users:
# #     user.age = 25
# #     print(f'Имя: {user.name}, Возраст: {user.age}')
# #
# # session.commit()
