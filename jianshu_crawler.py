#!python3
# --*-- coding: utf-8 --*--

# get users information from the website of jianshu

# http://www.jianshu.com/recommendations/users?page=1  推荐用户列表
# http://www.jianshu.com/u/5SqsuF?order_by=shared_at&page=2 用户文章
import threading
from datetime import datetime
import time

import jianshu_orm
import re
from jianshu_orm import init_mysql, User, Article, Follower
import urllib.request
import urllib.parse
import bs4
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import queue

base_url = 'http://www.jianshu.com'
recommend_base_url = base_url + '/recommendations/users'
author_article_url = 'order_by=shared_at&page=%s'
author_base_url = base_url + '/u/'
is_parse_all_over = False

def start_crawling():
    global article_browser
    global follower_browser
    global myre
    article_browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')
    follower_browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')

    try:
        # Wide UCS-4 build
        myre = re.compile(u'['
                          u'\U0001F300-\U0001F64F'
                          u'\U0001F680-\U0001F6FF'
                          u'\u2600-\u2B55]+',
                          re.UNICODE)
    except re.error:
        # Narrow UCS-2 build
        myre = re.compile(u'('
                          u'\ud83c[\udf00-\udfff]|'
                          u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
                          u'[\u2600-\u2B55])+',
                          re.UNICODE)
    # browser.set_page_load_timeout(30)
    # browser.implicitly_wait(20)
    init_mysql()
    _get_recommend_list()

def _get_recommend_list():
    has_data = True
    page_index = 1
    # global article_thread
    # global follower_thread
    # article_thread = ParserThread('article_thread', _get_author_articles)
    # follower_thread = ParserThread('follower_thread', _get_author_followers)
    # article_thread.start()
    # follower_thread.start()
    try:
        while has_data:
            html_text = _get_html_inner_text(recommend_base_url + '?page=' + str(page_index))
            if html_text is None:
                continue
            soup = bs4.BeautifulSoup(html_text, 'html.parser')
            elems = soup.select('div.col-xs-8 div.wrap')
            for elem in elems:
                # aElem = elem.findChild('a')
                # author_url = aElem.get('href')
                author_url = elem.a.get('href')

                author_url = base_url + author_url
                author = _get_author_full_info(author_url)
                if author is not None:
                    for follower in author.followers:
                        author_url = author_base_url + follower.follower_id
                        _get_author_full_info(author_url)

        global is_parse_all_over
        is_parse_all_over = True

        # article_thread.join()
        # follower_thread.join()
    except Exception as error:
        raise error

def _get_author_full_info(author_url):
    try:
        session = jianshu_orm.DBSession()
        author = _get_author_base_info(author_url, session)
        if author is not None:
            f = author.followers

        if author is not None:
            if len(author.articles) != author.article_count and not author.is_article_complete:
                global article_thread
                article_thread.add_author(author)
                # _get_author_articles(author, session)
            if len(author.followers) != author.follower_count and not author.is_follower_complete:
                global follower_thread
                follower_thread.add_author(author)
                # _get_author_followers(author, session)
        session.close()
    except Exception as error:
        raise error
    return author

def _get_author_base_info(author_url, session):
    print('********************get author base info start**********************')
    author_id = author_url.split('/').pop()
    if author_id is None:
        return None
    list = session.query(User).filter(User.id == author_id).all()
    if list is not None and len(list) > 0:
        return list[0]

    print('author_url: ' + author_url)
    html_text = _get_html_inner_text(author_url)
    if html_text is None:
        return None
    parent_soup = bs4.BeautifulSoup(html_text, 'html.parser')
    # 头像
    imageElm = parent_soup.select('div.main-top a.avatar img')[0]
    author_image = 'http:' + imageElm.get('src')
    # 名字
    nameElm = parent_soup.select('div.main-top div.title a')[0]
    author_url = base_url + nameElm.get('href')
    author_name = nameElm.text
    # 个人介绍
    noteElem = parent_soup.select('div.description div.js-intro')[0]
    author_note = noteElem.text

    extraElms = parent_soup.select('div.main-top div.info ul li')
    # 作者关注的人数和url
    following_url = base_url + extraElms[0].div.a['href']
    author_following_count = int(extraElms[0].div.a.p.string)
    # 关注作者的人数
    follower_url = base_url + extraElms[1].div.a['href']
    author_follower_count = int(extraElms[1].div.a.p.string)
    # 文章数量
    article_url = base_url + extraElms[2].div.a['href']
    author_article_count = int(extraElms[2].div.a.p.string)
    # 字数
    author_word_count = int(extraElms[3].div.p.string)
    # 点赞数
    author_like_count = int(extraElms[4].div.p.string)

    print(
        'Author: %s,\n Following: %s, \nFollowers: %s, \nArticle: %s, \nWords: %s, \nLike: %s, \nFollowing_Url: %s, \nFollower_url: %s, \nArticle_url: %s' % (
            author_name, author_following_count, author_follower_count, author_article_count, author_word_count,
            author_like_count, following_url, follower_url, article_url))

    author = User()
    author.like_count = author_like_count
    author.name = _cut_long_str(_replace_spacial_char(author_name), 100)
    author.image = author_image
    author.url = author_url
    author.following_count = author_following_count
    author.follower_count = author_follower_count
    author.article_count = author_article_count
    author.word_count = author_word_count
    author.id = author_url.split('/').pop()
    author.note = _cut_long_str(_replace_spacial_char(author_note), 255)
    author.follower_url = follower_url
    author.following_url = following_url
    author.is_follower_complete = author_follower_count == 0
    author.is_article_complete = author_article_count == 0

    commit2db(author, session)
    print('********************get author base info end**********************')
    time.sleep(3)
    return author

def _get_author_articles(author, session):
    print('********************get author article list start**********************')
    # 获取文章列表
    allow_none_times = 20
    pageIndex = 1
    if author.article_count > 0:
        article_urls = []
        while (len(article_urls) < author.article_count) and (allow_none_times > 0):
            if pageIndex == 1:
                html_text = _get_html_inner_text(author.url)
            else:
                html_text = _get_browser_inner_text(article_browser, author.url)

            parent_soup = bs4.BeautifulSoup(html_text, 'html.parser')
            if not _parse_articles(author, parent_soup, article_urls, session):
                allow_none_times -= 1
            else:
                allow_none_times = 20
                commit2db(author, session)
            pageIndex += 1
        author.is_article_complete = True
        if author.is_follower_complete:
            author.is_all_complete = True
        commit2db(author, session)
    print('********************get author article list end**********************')

def _get_author_followers(author, session):
    print('********************get author follower info start**********************')
    # 获取关注作者的用户列表
    allow_none_times = 20
    pageIndex = 1
    follower_ids = []
    while (len(follower_ids) < author.follower_count) and allow_none_times > 0:
        follower_html = ''
        if author.follower_url is None:
            author.follower_url = 'http://www.jianshu.com/users/%s/followers' % author.id
        if pageIndex == 1:
            follower_html = _get_html_inner_text(author.follower_url)
        else:
            follower_html = _get_browser_inner_text(follower_browser, author.follower_url)
        pageIndex += 1
        parent_soup = bs4.BeautifulSoup(follower_html)
        if not _parse_followers(author, parent_soup, follower_ids, session):
            allow_none_times -= 1
        else:
            allow_none_times = 20
            commit2db(author, session)
    author.is_follower_complete = True
    if author.is_article_complete:
        author.is_all_complete = True
    commit2db(author, session)
    print('********************get author follower info end**********************')

def commit2db(author, session):
    session.add(author)
    session.commit()

def _parse_followers(author, parent_soup, follower_ids, session):
    src_len = len(follower_ids)
    followerElems = parent_soup.select('div#list-container ul.user-list li')
    print('=============src: %s===new: new: %s============' % (src_len, len(followerElems)))
    if len(followerElems) <= src_len:
        return False
    for elem in followerElems[src_len:]:
        nameElem = elem.find('a', class_='name')
        follower_name = nameElem.text
        follower_id = nameElem.get('href').split('/').pop()
        if has_follower_in_mysql(author.id, follower_id, session):
            if follower_id not in follower_ids:
                follower_ids.append(follower_id)
            continue
        if follower_id not in follower_ids:
            follower = Follower(follower_id, follower_name, author.name)
            follower_ids.append(follower_id)
            author.followers.append(follower)
            print('Following: %s, %s, <------- follower: %s, %s' % (
                author.id, author.name, follower.follower_id, follower.follower_name))
    print('=============src: %s===new: new: %s============' % (src_len, len(followerElems)))
    return len(follower_ids) > src_len

def has_follower_in_mysql(following_id, follower_id, session):
    if following_id is None or follower_id is None:
        return True
    list = session.query(Follower).filter(
        Follower.follower_id == follower_id and Follower.following_id == following_id).all()
    if list is None or len(list) == 0:
        return False
    return True

def _parse_articles(author, parent_soup, article_urls, session):
    src_len = len(article_urls)
    articleElems = parent_soup.select('div#list-container ul.note-list li')
    print('=============src: %s===new: new: %s============' % (src_len, len(articleElems)))
    if len(articleElems) <= src_len:
        return False
    for elem in articleElems[src_len:]:
        soup = bs4.BeautifulSoup(str(elem))
        titleElem = soup.find('a', class_='title')
        href = titleElem.get('href')
        if href in article_urls:
            continue
        article_urls.append(href)
        url = base_url + href
        article_id = url.split('/').pop()
        if has_article_in_mysql(article_id, session):
            continue
        title = _cut_long_str(_replace_spacial_char(titleElem.text), 100)
        summaryElem = soup.find('p', class_='abstract')
        summary = _cut_long_str(_replace_spacial_char(summaryElem.text.strip()), 255)
        readElem = soup.select('div.content div.meta  a')[0]
        read_count = int(readElem.text)
        comment_count = 0
        commentElem = readElem.find_next_sibling('a')
        if commentElem != None:
            comment_count = int(commentElem.text)
        like_count = 0
        likeElem = readElem.find_next_sibling('span')
        if likeElem != None:
            like_count = int(likeElem.text)
        moneyElem = likeElem.find_next_sibling('span')
        money_count = 0
        if moneyElem != None:
            money_count = int(moneyElem.text)
        timeElem = soup.find('span', class_='time')
        time_text = timeElem.get('data-shared-at')
        # 2017 - 11 - 27 T23:36:33 + 08: 00
        created_at = datetime.strptime(time_text, '%Y-%m-%dT%H:%M:%S+08:00')
        article = Article(article_id, title, summary, url, created_at, read_count, comment_count,
                          like_count,
                          money_count, author.name)
        author.articles.append(article)
        print('title: %s, \nsummary:%s, \nurl:%s, \ntime:%s, \nread: %s, \ncomment:%s, \nlike:%s, \nmoney:%s' % (
            title, summary, url, created_at, read_count, comment_count, like_count, money_count))
    print('=============src: %s===new: new: %s============' % (src_len, len(articleElems)))
    return len(article_urls) > src_len

def has_article_in_mysql(article_id, session):
    if article_id is None:
        return True
    list = session.query(Article).filter(Article.id == article_id).all()
    if list is None or len(list) == 0:
        return False
    return True

def _get_html_inner_text(url):
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        with urllib.request.urlopen(req) as f:
            print(type(f))
            print('status: ', f.status, f.reason)
            html_text = f.read().decode('utf-8')
            return html_text
    except Exception as ex:
        print('<_get_html_inner_text> error: ' + str(ex))
        return None

def _get_browser_inner_text(browser, referer):
    try:
        WebDriverWait(browser, 30).until(waiter(browser, referer))
    except Exception as ex:
        print(str(ex))
        scroll(browser)
    selenium_html = browser.execute_script("return document.documentElement.outerHTML")
    return selenium_html

def scroll(browser):
    # 第二种可以滚动到底部的方法
    # browser.maximize_window()
    # time.sleep(3)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    # browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # 第一种滚动到底部的方法
    # driver.execute_script("""
    #     (function () {
    #         var y = document.body.scrollTop;
    #         var step = 100;
    #         window.scroll(0, y);
    #
    #         function f() {
    #             if (y < document.body.scrollHeight) {
    #                 y += step;
    #                 window.scroll(0, y);
    #                 setTimeout(f, 50);
    #             }
    #             else {
    #                 window.scroll(0, y);
    #                 document.title += "scroll-done";
    #             }
    #         }
    #         setTimeout(f, 1000);
    #     })();
    # """)

def _replace_spacial_char(src_text):
    global myre
    new_text = myre.sub(' ', src_text)
    print(new_text)
    return new_text

def _cut_long_str(src_text, max_len):
    if len(src_text) < max_len:
        return src_text
    return ''.join(src_text[0:max_len])

class waiter(object):
    def __init__(self, browser, referer):
        self.browser = browser
        self.referer = referer

    def __call__(self, *args, **kwargs):
        print('*****call*****')
        if self.browser.current_url != self.referer:
            self.browser.get(self.referer)
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        return True

class ParserThread(threading.Thread):
    def __init__(self, name, func):
        super(ParserThread, self).__init__()
        self.parsing_queue = queue.Queue()
        self.func = func
        self.name = name

    def run(self):
        global is_parse_all_over
        while not self.parsing_queue.empty() or not is_parse_all_over:
            print('=============1=============' + self.name)
            print('=====queue length: ' + str(self.parsing_queue.qsize()))
            if self.parsing_queue.empty():
                print('=============2=============' + self.name)
                time.sleep(3)
                continue
            print('=============3=============' + self.name)
            try:
                author = self.parsing_queue.get()
                session = jianshu_orm.DBSession()
                try:
                    self.func(author, session)
                finally:
                    session.close()
                print('=============4=============' + self.name)
            except Exception as error:
                print(str(error))

    def add_author(self, author):
        self.parsing_queue.put(author)
