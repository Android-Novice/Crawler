from datetime import datetime
import baidu_crawler
import jianshu_orm
import jianshu_crawler
from jianshu_crawler import start_crawling

if __name__ == '__main__':
    # import re
    #
    # try:
    #     # Wide UCS-4 build
    #     myre = re.compile(u'['
    #                       u'\U0001F300-\U0001F64F'
    #                       u'\U0001F680-\U0001F6FF'
    #                       u'\u2600-\u2B55]+',
    #                       re.UNICODE)
    # except re.error:
    #     # Narrow UCS-2 build
    #     myre = re.compile(u'('
    #                       u'\ud83c[\udf00-\udfff]|'
    #                       u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
    #                       u'[\u2600-\u2B55])+',
    #                       re.UNICODE)
    # text = '刚刚玩简书，发现这里是文艺青年的天堂阿☺ 我是一名摄影师，也喜欢文字，如果写的浅显，有的时候也会词穷，谢谢大家指正，也可以关注我的新浪微博@摄影师杨书坤📷'
    # text1 = '4月14日·打卡🔖芷对你说'
    # text2 = '😊不在的时候可加v15160324314'
    # text3 = '大家有喜欢萌萌头像的吗😊想要属于自己的扣1无偿制作'
    # text4 = '闪亮护眼小百科关于迎风流泪的小科普1⃣️人们长时间患沙眼、慢性结膜炎或慢性鼻炎，就会累及鼻泪管粘膜，造成鼻泪管阻塞。️泪液积聚于泪囊中，眼泪就会不断流出。️如被冷风一吹，泪腺分泌会增多，所以流泪也就会更多了。️泪为人体五液之一，若久流泪不止，难辨物色，甚至失明。️可见迎风流泪并非小病，应及早就治。闪亮护眼贴会让你有意想不到的收获, '
    # print(len(text4))
    # text = myre.sub('', text)
    # text1 = myre.sub('', text1)
    # text2 = myre.sub('', text2)
    # text3 = myre.sub('', text3)
    # text4 = myre.sub('', text4)
    # text4 = myre.sub('', text4)
    # text4 = myre.sub('', text4)
    # text4 = ''.join(text4[0:100])
    # print(text4)
    # print(111)

    start_crawling()

    # text = '刚刚玩简书，发现这里是文艺青年的天堂阿☺ 我是一名摄影师，也喜欢文字，如果写的浅显，有的时候也会词穷，谢谢大家指正，也可以关注我的新浪微博@摄影师杨书坤📷'
    # text = text.replace('📷', '')

    # text = '4月14日·打卡🔖芷对你说'
    # text = text.replace('📷', ' ')
    # text = text.replace('🔖',' ')
    # print('📷'== '🔖')
    # text = jianshu_crawler._replace_spacial_char(text)

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
    pass
