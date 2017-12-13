#!python3
# --*-- coding: utf-8 --*--

# get users information from the website of jianshu

# http://www.jianshu.com/recommendations/users?page=1  推荐用户列表
# http://www.jianshu.com/u/5SqsuF?order_by=shared_at&page=2 用户文章
import shutil
import threading
from datetime import datetime
import time
import logging
import gc
import random
import jianshu_orm
import os
from jianshu_orm import init_mysql, User, Article, Follower, ParsingItem
import urllib.request
import urllib.parse
import bs4
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from enum import Enum

base_url = 'http://www.jianshu.com'
recommend_base_url = base_url + '/recommendations/users'
author_article_url = base_url + '/u/%s?order_by=shared_at&page=%s'
author_follower_url = base_url + '/users/%s/followers?page=%s'
author_base_url = base_url + '/u/'
is_parse_all_over = False

def start_crawling():
    logging.debug('start crawling....')
    delete_temp_folders()

    # global article_browser
    # global follower_browser
    # article_browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')
    # follower_browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')

    # browser.set_page_load_timeout(30)
    # browser.implicitly_wait(20)
    init_mysql()
    session = jianshu_orm.get_db_session()
    list = session.query(ParsingItem).filter(ParsingItem.is_parsed == 1).all()
    if list is not None and len(list) > 0:
        for item in list:
            item.is_parsed = 0
        session.flush()
        session.commit()
    _get_recommend_list()

def _get_recommend_list():
    global scopedSession
    scopedSession = jianshu_orm.get_db_scoped_session()

    has_data = True
    page_index = 1
    article_thread = ParserThread(ThreadKind.Article, _get_author_articles)
    follower_thread = ParserThread(ThreadKind.Follower, _get_author_followers)
    rlock = threading.RLock()
    author_thread_1 = AuthorThread(_get_author_base_info, rlock)
    author_thread_2 = AuthorThread(_get_author_base_info, rlock)
    author_thread_3 = AuthorThread(_get_author_base_info, rlock)
    article_thread.start()
    follower_thread.start()
    author_thread_1.start()
    author_thread_2.start()
    author_thread_3.start()

    try:
        while has_data:
            html_text = _get_html_inner_text(recommend_base_url + '?page=' + str(page_index))
            if html_text is None:
                continue
            soup = bs4.BeautifulSoup(html_text, 'html.parser')
            elems = soup.select('div.col-xs-8 div.wrap')
            for elem in elems:
                author_url = elem.a.get('href')
                author_id = author_url.split('/').pop()
                _get_author_full_info(author_id)
            del html_text, soup, elems
            page_index += 1
            time.sleep(10)
            gc.collect()

        global is_parse_all_over
        is_parse_all_over = True

        article_thread.join()
        follower_thread.join()
        author_thread_1.join()
        author_thread_2.join()
        author_thread_3.join()
    except Exception as error:
        logging.error('<Exception> _get_recommend_list: \n')
        logging.error(str(error))

def _get_author_full_info(author_id):
    try:
        session = jianshu_orm.get_db_session()
        author = _get_author_base_info(author_id, session)
        session.close()
        session.prune()
        del session
        return author
    except Exception as error:
        logging.error('<Exception> get-author-full-info:\n')
        logging.error(str(error))
    return None

def _get_author_base_info(author_id, session):
    if author_id is None:
        return None
    item = session.query(User).filter(User.id == author_id).first()
    if item is not None:
        return item

    print('********************get author base info start**********************')
    author_url = author_base_url + author_id
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

    session.add(author)
    session.flush()
    session.commit()
    time.sleep(2)
    print('********************get author base info end**********************')
    return author

def _get_author_articles(author, session):
    print('********************get author article list start**********************')
    if author.article_count > 0:
        pageIndex = 1
        article_urls = []
        while True:
            url = author_article_url % (author.id, pageIndex)
            html_text = _get_html_inner_text(url)
            if html_text is None:
                break
            parent_soup = bs4.BeautifulSoup(html_text, 'html.parser')
            if not _parse_articles(author, parent_soup, article_urls, session):
                break
            else:
                session.flush()
                session.commit()
                time.sleep(random.random())
            pageIndex += 1

        if author.article_count < len(article_urls):
            author.article_count = len(article_urls)
    author.is_article_complete = True
    if author.is_follower_complete:
        author.is_all_complete = True
    session.flush()
    session.commit()
    print('********************get author article list end**********************')

def _get_author_followers(author, session):
    print('********************get author follower info start**********************')
    # 获取关注作者的用户列表
    if author.follower_count > 0:
        pageIndex = 1
        follower_ids = []
        while True:
            url = author_follower_url % (author.id, pageIndex)
            follower_html = _get_html_inner_text(url)
            if follower_html is None:
                break
            parent_soup = bs4.BeautifulSoup(follower_html, 'html.parser')
            if not _parse_followers(author, parent_soup, follower_ids, session):
                break
            else:
                session.flush()
                session.commit()
                time.sleep(random.random())
            pageIndex += 1
        if author.follower_count < len(follower_ids):
            author.follower_count = len(follower_ids)
    author.is_follower_complete = True
    if author.is_article_complete:
        author.is_all_complete = True
    session.flush()
    session.commit()
    print('********************get author follower info end**********************')

def _parse_followers(author, parent_soup, follower_ids, session):
    src_len = len(follower_ids)
    followerElems = parent_soup.select('div#list-container ul.user-list li')
    print('======Follower=======src: %s===new: %s=====show:%s=====Name:%s %s==' % (
        src_len, len(followerElems), author.follower_count, author.name, author.id))
    for elem in followerElems:
        nameElem = elem.find('a', class_='name')
        follower_id = nameElem.get('href').split('/').pop()
        if author.id is None or follower_id is None:
            continue
        if follower_id in follower_ids:
            continue
        follower_ids.append(follower_id)
        item = session.query(Follower).filter(
            Follower.follower_id == follower_id and Follower.following_id == author.id).first()
        if item is not None:
            continue

        follower_name = _replace_spacial_char(nameElem.text)
        follower = Follower(follower_id, follower_name, author.name)
        follower.following_id = author.id
        session.add(follower)
        _add_parsing_item(follower_id, session)
        print('Following: %s, %s, <------- follower: %s, %s' % (
            author.id, author.name, follower.follower_id, follower.follower_name))
    print('======Follower=======src: %s===afterparsing: %s=====show:%s=====Name:%s %s==' % (
        src_len, len(follower_ids), author.follower_count, author.name, author.id))
    return len(follower_ids) > src_len

def _add_parsing_item(follower_id, session):
    item = session.query(jianshu_orm.ParsingItem).filter(jianshu_orm.ParsingItem.author_id == follower_id).first()
    if item is None:
        item = jianshu_orm.ParsingItem(follower_id)
        session.add(item)

def _parse_articles(author, parent_soup, article_urls, session):
    src_len = len(article_urls)
    articleElems = parent_soup.select('div#list-container ul.note-list li')
    print('====Article=========src: %s===new: %s======show: %s===name: %s, %s===' % (
        src_len, len(articleElems), author.article_count, author.name, author.id))
    for elem in articleElems:
        soup = bs4.BeautifulSoup(str(elem), 'html.parser')
        titleElem = soup.find('a', class_='title')
        if titleElem is None:
            continue
        href = titleElem.get('href')
        if href in article_urls:
            continue
        article_urls.append(href)
        url = base_url + href
        article_id = url.split('/').pop()
        if article_id is None:
            continue
        item = session.query(Article).filter(Article.id == article_id).first()
        if item is not None:
            continue
        title = _cut_long_str(_replace_spacial_char(titleElem.text), 100)
        summaryElem = soup.find('p', class_='abstract')
        if summaryElem is None:
            continue
        summary = _cut_long_str(_replace_spacial_char(summaryElem.text.strip()), 255)
        readElem = soup.select('div.content div.meta  a')[0]
        if readElem.text.strip().isdecimal():
            read_count = int(readElem.text)
        else:
            continue
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
                          like_count, money_count, author.name)
        article.author_id = author.id
        session.add(article)
        print('title: %s, \nsummary:%s, \nurl:%s, \ntime:%s, \nread: %s, \ncomment:%s, \nlike:%s, \nmoney:%s' % (
            title, summary, url, created_at, read_count, comment_count, like_count, money_count))
    print('====Article=========src: %s===afterparsing: %s======show: %s===name: %s, %s===' % (
        src_len, len(article_urls), author.article_count, author.name, author.id))
    return len(article_urls) > src_len

def _get_html_inner_text(url):
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        with urllib.request.urlopen(req) as f:
            print(type(f))
            print('status: ', f.status, f.reason)
            if f.url != url:
                logging.warning('<Warning> url doest\'t match: src: %s, \n, new: f.url: %s' % (url, f.url))
            if 'timeline' in f.url:
                html_text = None
            else:
                html_text = f.read().decode('utf-8')
            del req
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
    str_list = list(src_text)
    index = -1
    for i in str_list:
        index += 1
        if ord(i) > 120000:
            print('****************************************************************src: %s, ord: %s' % (i, ord(i)))
            str_list[index] = ''
    new_text = ''.join(str_list)
    del str_list
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

def delete_temp_folders():
    try:
        root = os.path.dirname(os.getenv('appdata'))
        temp_dir = os.path.join(root, r'local\temp')
        for sub in os.listdir(temp_dir):
            sub = os.path.join(temp_dir, sub)
            if os.path.isdir(sub) and 'scoped_dir' in sub:
                shutil.rmtree(sub, True)
    except Exception as error:
        logging.error('<Exception> get-delete_temp_folders:\n')
        logging.error(str(error))

class ThreadKind(Enum):
    Article = 1
    Follower = 2

class ParserThread(threading.Thread):
    def __init__(self, thread_kind, func):
        super(ParserThread, self).__init__()
        self.func = func
        self.thread_kind = thread_kind
        if self.thread_kind == ThreadKind.Follower:
            self.name = 'follower_thread'
        else:
            self.name = 'article_thread'

    def run(self):
        global is_parse_all_over
        parsing_item_is_none = False
        while not is_parse_all_over or not parsing_item_is_none:
            print('=============1=============' + self.name)
            try:
                session = jianshu_orm.get_db_session()
                if self.thread_kind == ThreadKind.Follower:
                    author = session.query(User).filter(User.is_follower_complete == 0).limit(1).first()
                else:
                    author = session.query(User).filter(User.is_article_complete == 0).limit(1).first()
                parsing_item_is_none = author is None
                if author is None:
                    time.sleep(3)
                    continue
                self.func(author, session)
                print('=============4=============' + self.name)
            except Exception as error:
                logging.error('<Exception> ParserThread: %s\n' % self.name)
                logging.error(str(error))
            finally:
                session.close()
                session.prune()
                del session
                del author

class AuthorThread(threading.Thread):
    def __init__(self, func, rlock):
        super(AuthorThread, self).__init__()
        self.func = func
        self.rlock = rlock
        self.name = 'author_thread'

    def run(self):
        global is_parse_all_over
        parsing_author_is_none = False
        while not is_parse_all_over or not parsing_author_is_none:
            print('=============1=============' + self.name)
            try:
                session = jianshu_orm.get_db_session()
                self.rlock.acquire()
                item = session.query(ParsingItem).filter(ParsingItem.is_parsed == 0).limit(1).first()
                parsing_author_is_none = item is None
                if item is None:
                    time.sleep(3)
                    self.rlock.release()
                    continue
                item.is_parsed = 1
                session.flush()
                session.commit()
                self.rlock.release()
                self.func(item.author_id, session)
                print('=============2=============' + self.name)
                item.is_parsed = 2
                session.flush()
                session.commit()
            except Exception as error:
                logging.error('<Exception> AuthorThread: %s\n' % self.name)
                logging.error(str(error))
            finally:
                session.close()
                session.prune()
                del session
                del item

# *****************************Obsoleted****************************************

def _get_author_articles_backup(author, session):
    print('********************get author article list start**********************')
    # 获取文章列表
    allow_none_times = 15
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
                time.sleep(1)
            else:
                allow_none_times = 15
                session.flush()
                session.commit()
            pageIndex += 1
            del html_text, parent_soup
        author.is_article_complete = True
        if author.is_follower_complete:
            author.is_all_complete = True
        session.flush()
        session.commit()
    print('********************get author article list end**********************')

def _get_author_followers_backup(author, session):
    print('********************get author follower info start**********************')
    # 获取关注作者的用户列表
    allow_none_times = 15
    pageIndex = 1
    follower_ids = []
    while (len(follower_ids) < author.follower_count) and allow_none_times > 0:
        if author.follower_url is None:
            author.follower_url = 'http://www.jianshu.com/users/%s/followers' % author.id
        if pageIndex == 1:
            follower_html = _get_html_inner_text(author.follower_url)
        else:
            follower_html = _get_browser_inner_text(follower_browser, author.follower_url)
        pageIndex += 1
        parent_soup = bs4.BeautifulSoup(follower_html, 'html.parser')
        if not _parse_followers(author, parent_soup, follower_ids, session):
            allow_none_times -= 1
            time.sleep(1)
        else:
            allow_none_times = 15
            session.flush()
            session.commit()
        del parent_soup, follower_html
    author.is_follower_complete = True
    if author.is_article_complete:
        author.is_all_complete = True
    session.flush()
    session.commit()
    print('********************get author follower info end**********************')

def _parse_followers_backup(author, parent_soup, follower_ids, session):
    src_len = len(follower_ids)
    followerElems = parent_soup.select('div#list-container ul.user-list li')
    print('======Follower=======src: %s===new: %s=====show:%s=======' % (
        src_len, len(followerElems), author.follower_count))
    if len(followerElems) <= src_len:
        return False
    for elem in followerElems[src_len:]:
        nameElem = elem.find('a', class_='name')
        follower_name = _replace_spacial_char(nameElem.text)
        follower_id = nameElem.get('href').split('/').pop()

        if author.id is None or follower_id is None:
            continue
        item = session.query(Follower).filter(
            Follower.follower_id == follower_id and Follower.following_id == author.id).first()
        if item is not None:
            if follower_id not in follower_ids:
                follower_ids.append(follower_id)
            continue

        if follower_id not in follower_ids:
            follower = Follower(follower_id, follower_name, author.name)
            follower_ids.append(follower_id)
            # author.followers.append(follower)
            follower.following_id = author.id
            session.add(follower)

            _add_parsing_item(follower_id, session)
            print('Following: %s, %s, <------- follower: %s, %s' % (
                author.id, author.name, follower.follower_id, follower.follower_name))
            del follower
    print('======Follower=======src: %s===new: %s=====show:%s=======' % (
        src_len, len(followerElems), author.follower_count))
    del followerElems
    return len(follower_ids) > src_len

def _parse_articles_backup(author, parent_soup, article_urls, session):
    src_len = len(article_urls)
    articleElems = parent_soup.select('div#list-container ul.note-list li')
    print('====Article=========src: %s===new: %s======show: %s======' % (
        src_len, len(articleElems), author.article_count))
    if len(articleElems) <= src_len:
        del articleElems
        return False
    for elem in articleElems[src_len:]:
        soup = bs4.BeautifulSoup(str(elem), 'html.parser')
        titleElem = soup.find('a', class_='title')
        href = titleElem.get('href')
        if href in article_urls:
            continue
        article_urls.append(href)
        url = base_url + href
        article_id = url.split('/').pop()
        if article_id is None:
            continue
        item = session.query(Article).filter(Article.id == article_id).first()
        if item is not None:
            continue
        title = _cut_long_str(_replace_spacial_char(titleElem.text), 100)
        summaryElem = soup.find('p', class_='abstract')
        if summaryElem is None:
            continue
        summary = _cut_long_str(_replace_spacial_char(summaryElem.text.strip()), 255)
        readElem = soup.select('div.content div.meta  a')[0]
        if readElem.text.strip().isdecimal():
            read_count = int(readElem.text)
        else:
            continue
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
                          like_count, money_count, author.name)
        article.author_id = author.id
        session.add(article)
        del soup
        # author.articles.append(article)
        print('title: %s, \nsummary:%s, \nurl:%s, \ntime:%s, \nread: %s, \ncomment:%s, \nlike:%s, \nmoney:%s' % (
            title, summary, url, created_at, read_count, comment_count, like_count, money_count))
    print('====Article=========src: %s===new: %s======show: %s======' % (
        src_len, len(articleElems), author.article_count))
    del articleElems
    return len(article_urls) > src_len
