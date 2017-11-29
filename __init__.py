from datetime import datetime
import baidu_crawler
import jianshu_orm
import jianshu_crawler
from jianshu_crawler import start_crawling

if __name__ == '__main__':
    start_crawling()

    # text = '刚刚玩简书，发现这里是文艺青年的天堂阿☺ 我是一名摄影师，也喜欢文字，如果写的浅显，有的时候也会词穷，谢谢大家指正，也可以关注我的新浪微博@摄影师杨书坤📷'
    # text = text.replace('📷', '')

    # jianshu_orm.init_mysql()
    # user = jianshu_orm.User()
    # user.id = '1'
    # user.like_count = 1
    # user.word_count = 10
    # user.article_count = 2
    # user.follower_count = 0
    # user.following_count = 1
    # user.name = 'test'
    # user.url = ''
    # user.image = 'about:blank'
    # user.articles = [
    #     jianshu_orm.Article('11', 'title', 'summary', '', datetime.now(), 100, 1000, 10000, 10, user.name),
    #     jianshu_orm.Article('211', '2title', '2summary', '', datetime.now(), 2100, 21000, 210000, 210, user.name)
    # ]
    # user.followers = [
    #     jianshu_orm.Follower('111111', 'follower', user.name),
    #     jianshu_orm.Follower('2111111', '2follower', user.name)
    # ]
    #
    # print('*********************************')
    # session = jianshu_orm.DBSession()
    # session.add(user)
    # session.commit()
    #
    # user.followers.append(jianshu_orm.Follower('31111111','Follower3', user.name))
    # user.articles.append(jianshu_orm.Article('311', '3title', '3summary', '', datetime.now(), 3100, 31000, 310000, 310, user.name))
    # session.add(user)
    # session.commit()

    # baidu_crawler.baiduWebCrawling('美女')
