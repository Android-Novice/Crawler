import pymysql
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Text, Index, UniqueConstraint, \
    Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

def init_mysql():
    try:
        # conn = aiomysql.connect(user='root',password='123456',db='my_blog')
        conn = pymysql.connect(user='root', password='123456', charset='utf8')
        cur = conn.cursor()
        create_db = 'create database if not EXISTS jianshuwebsite'
        # drop_table = 'drop table if EXISTS my_blog.users '
        # create_users_table = 'CREATE TABLE IF NOT EXISTS my_blog.users(id varchar(50) not null primary key, email VARCHAR(50) NOT NULL, password VARCHAR(50) NOT NULL,' \
        #                      'is_admin TINYINT, name VARCHAR(50) NOT NULL, image VARCHAR(500), created_at REAL, age TINYINT, is_male bool, note TEXT)'
        # create_blogs_table = 'CREATE TABLE IF NOT EXISTS my_blog.blogs(id varchar(50) not null primary key, user_id VARCHAR(50) NOT NULL, user_name VARCHAR(50) NOT NULL,' \
        #                      'title VARCHAR(50) NOT NULL, summary VARCHAR(500), content TEXT NOT NULL, created_at REAL)'
        # create_comments_table = 'CREATE TABLE IF NOT EXISTS my_blog.comments(id varchar(50) not null primary key, user_id VARCHAR(50) NOT NULL, ' \
        #                         'user_name VARCHAR(50) NOT NULL, blog_id VARCHAR(50) NOT NULL, content TEXT NOT NULL, created_at REAL)'
        cur.execute(create_db)
        # cur.execute(drop_table)
        # cur.execute(create_users_table)
        # cur.execute(create_blogs_table)
        # cur.execute(create_comments_table)
        cur.close()
        conn.close()

        Base.metadata.create_all(engine)
    except Exception as e:
        raise

engine = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/jianshuwebsite?charset=utf8', echo=True)
Base = declarative_base()
DBSession = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(String(100), primary_key=True, nullable=False)
    name = Column(String(100), unique=True)
    following_count = Column(Integer)
    following_url = Column(String(255))
    follower_count = Column(Integer)
    follower_url = Column(String(255))
    article_count = Column(Integer)
    word_count = Column(Integer)
    like_count = Column(Integer)
    image = Column(String(255))
    note = Column(String(255))
    url = Column(String(255))
    is_over = Column(Boolean, default=False)

    # articles = relationship('Article', primaryjoin='users.c.id==articles.c.author_id')
    # followers = relationship('Follower', primaryjoin='users.c.id==followers.c.following_id')
    articles = relationship('Article', primaryjoin='User.id==Article.author_id')
    followers = relationship('Follower', primaryjoin='User.id==Follower.following_id')

    __table_args__ = (
        UniqueConstraint('id', 'name', name='uix_id_name'),
        Index('ix_id_name', 'name'),
    )

    def __repr__(self):
        return '<User(id=%s, name=%s, following=%s, follower=%s, article=%s, word=%s, like=%s)>' % (
            self.id, self.name, self.following_count, self.follower_count, self.article_count, self.word_count,
            self.like_count)

class Article(Base):
    __tablename__ = 'articles'

    id = Column(String(100), primary_key=True, nullable=False)
    title = Column(String(100))
    summary = Column(Text)
    created_at = Column(DateTime)
    read_count = Column(Integer)
    comment_count = Column(Integer)
    like_count = Column(Integer)
    money_count = Column(Integer)
    url = Column(String(255))
    author_name = Column(String(100), ForeignKey('users.name'))
    author_id = Column(String(100), ForeignKey('users.id'))

    def __repr__(self):
        return '<Article(author:%s, title=%s)>' % (self.author_name, self.title)

    def __init__(self, id, title, summary, url, created_at, read_count, comment_count, like_count, money_count,
                 author_name):
        self.id = id
        self.title = title
        self.summary = summary
        self.url = url
        self.created_at = created_at
        self.read_count = read_count
        self.comment_count = comment_count
        self.like_count = like_count
        self.money_count = money_count
        self.author_name = author_name

# 每个用户的关注者列表
class Follower(Base):
    __tablename__ = 'followers'

    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    following_id = Column(String(100), ForeignKey('users.id'))
    following_name = Column(String(100), ForeignKey('users.name'))
    follower_id = Column(String(100))
    follower_name = Column(String(100))

    def __init__(self, follower_id, follower_name, following_name):
        self.follower_id = follower_id
        self.follower_name = follower_name
        self.following_name = following_name

    def __repr__(self):
        return '<Follower(follerer_id:%s, follower_name:%s)>' % (self.follower_id, self.follower_name)
