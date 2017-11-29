#!python3
# --*-- coding: utf-8 --*--

# get users information from the website of jianshu

# http://www.jianshu.com/recommendations/users?page=1  推荐用户列表
# http://www.jianshu.com/u/5SqsuF?order_by=shared_at&page=2 用户文章
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

base_url = 'http://www.jianshu.com'
recommend_base_url = base_url + '/recommendations/users'
author_article_url = 'order_by=shared_at&page=%s'
author_base_url = base_url + '/u/'

def start_crawling():
    global browser
    browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')
    browser.set_page_load_timeout(30)
    init_mysql()
    _get_recommend_list()

def _get_recommend_list():
    has_data = True
    page_index = 1
    session = jianshu_orm.DBSession()
    try:
        while has_data:
            html_text = _get_html_inner_text(recommend_base_url + '?page=' + str(page_index))
            soup = bs4.BeautifulSoup(html_text, 'html.parser')
            elems = soup.select('div.col-xs-8 div.wrap')
            for elem in elems:
                item_soup = bs4.BeautifulSoup(str(elem), 'html.parser')
                aElem = item_soup.select('a')[0]
                author_url = aElem.get('href')
                author_url = base_url + author_url
                author = _get_author_full_info(author_url, session)
                if author is not None:
                    for follower in author.followers:
                        author_url = author_base_url + follower.follower_id
                        _get_author_full_info(author_url, session)
    except Exception as error:
        session.close()
        raise error

def _get_author_full_info(author_url, session):
    author = _get_author_base_info(author_url, session)
    if author is not None:
        if len(author.articles) != author.article_count:
            _get_author_articles(author, session)
        if len(author.followers) != author.follower_count:
            _get_author_followers(author, session)
    return author

def _get_author_base_info(author_url, session):
    print('********************get author start**********************')
    author_id = author_url.split('/').pop()
    if author_id is None:
        return None
    list = session.query(User).filter(User.id == author_id).all()
    if list is not None and len(list) > 0:
        return list[0]

    print('author_url: ' + author_url)
    html_text = _get_html_inner_text(author_url)
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
    # 作者关注的人数和url
    extraElms = parent_soup.select('div.main-top div.info ul li')
    followingSoup = bs4.BeautifulSoup(str(extraElms[0]))
    followingElem = followingSoup.select('div.meta-block a')[0]
    countElem = followingElem.findChild('p')
    following_url = base_url + followingElem.get('href')
    author_following_count = int(countElem.text)
    # 关注作者的人数
    followerSoup = bs4.BeautifulSoup(str(extraElms[1]))
    followerElem = followerSoup.select('div.meta-block a')[0]
    countElem = followerElem.findChild('p')
    follower_url = base_url + followerElem.get('href')
    author_follower_count = int(countElem.text)
    # 文章数量
    articleSoup = bs4.BeautifulSoup(str(extraElms[2]))
    articleElem = articleSoup.select('div.meta-block a')[0]
    countElem = articleElem.findChild('p')
    article_url = base_url + articleElem.get('href')
    author_article_count = int(countElem.text)
    # 字数
    wordSoup = bs4.BeautifulSoup(str(extraElms[3]))
    wordElem = wordSoup.select('div.meta-block p')[0]
    author_word_count = int(wordElem.text)
    # 点赞数
    likeSoup = bs4.BeautifulSoup(str(extraElms[4]))
    likeElem = likeSoup.select('div.meta-block p')[0]
    author_like_count = int(likeElem.text)
    print(
        'Author: %s,\n Following: %s, \nFollowers: %s, \nArticle: %s, \nWords: %s, \nLike: %s, \nFollowing_Url: %s, \nFollower_url: %s, \nArticle_url: %s' % (
            author_name, author_following_count, author_follower_count, author_article_count, author_word_count,
            author_like_count, following_url, follower_url, article_url))

    author = User()
    author.like_count = author_like_count
    author.name = author_name
    author.image = author_image
    author.url = author_url
    author.following_count = author_following_count
    author.follower_count = author_follower_count
    author.article_count = author_article_count
    author.word_count = author_word_count
    author.id = author_url.split('/').pop()
    author.note = _replace_spacial_char(author_note)
    author.follower_url = follower_url
    author.following_url = following_url

    commit2db(author, session)

    # # 获取文章列表
    # allow_none_times = 20
    # pageIndex = 1
    # if author_article_count > 0:
    #     article_urls = []
    #     while (len(article_urls) < author_article_count) and (allow_none_times > 0):
    #         ret_value = True
    #         if pageIndex == 1:
    #             ret_value = _parse_articles(author, parent_soup, article_urls, session)
    #         else:
    #             next_article_url = author_url + '?' + (author_article_url % pageIndex)
    #             next_article_html_text = _get_browser_inner_text(author_url)
    #             parent_soup = bs4.BeautifulSoup(next_article_html_text, 'html.parser')
    #             ret_value = _parse_articles(author, parent_soup, article_urls, session)
    #         if not ret_value:
    #             allow_none_times -= 1
    #         else:
    #             allow_none_times = 20
    #             commit2db(author, session)
    #         pageIndex += 1

    # # 获取关注作者的用户列表
    # allow_none_times = 20
    # pageIndex = 1
    # follower_ids = []
    # while (len(follower_ids) < author_follower_count) and allow_none_times > 0:
    #     follower_html = ''
    #     if pageIndex == 1:
    #         follower_html = _get_html_inner_text(follower_url)
    #     else:
    #         follower_html = _get_browser_inner_text(follower_url)
    #     pageIndex += 1
    #     parent_soup = bs4.BeautifulSoup(follower_html)
    #     if not _parse_followers(author, parent_soup, follower_ids, session):
    #         allow_none_times -= 1
    #     else:
    #         allow_none_times = 20
    #         commit2db(author, session)

    print('********************get author end**********************')
    time.sleep(5)
    return author

def _get_author_articles(author, session):
    # 获取文章列表
    allow_none_times = 20
    pageIndex = 1
    if author.article_count > 0:
        article_urls = []
        while (len(article_urls) < author.article_count) and (allow_none_times > 0):
            if pageIndex == 1:
                # ret_value = _parse_articles(author, parent_soup, article_urls, session)
                html_text = _get_html_inner_text(author.url)
            else:
                # next_article_url = author.url + '?' + (author_article_url % pageIndex)
                html_text = _get_browser_inner_text(author.url)

            parent_soup = bs4.BeautifulSoup(html_text, 'html.parser')
            if not _parse_articles(author, parent_soup, article_urls, session):
                allow_none_times -= 1
            else:
                allow_none_times = 20
                commit2db(author, session)
            pageIndex += 1

def _get_author_followers(author, session):
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
            follower_html = _get_browser_inner_text(author.follower_url)
        pageIndex += 1
        parent_soup = bs4.BeautifulSoup(follower_html)
        if not _parse_followers(author, parent_soup, follower_ids, session):
            allow_none_times -= 1
        else:
            allow_none_times = 20
            commit2db(author, session)

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
            continue
        if follower_id not in follower_ids:
            follower = Follower(follower_id, follower_name, author.name)
            follower_ids.append(follower_id)
            author.followers.append(follower)
            print('Following: %s, %s, <------- follower: %s, %s' % (
                author.id, author.name, follower.follower_id, follower.follower_name))
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
        title = titleElem.text
        summaryElem = soup.find('p', class_='abstract')
        summary = summaryElem.text.strip()
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
        raise ex

def _get_browser_inner_text(referer):
    try:
        # if browser.current_url != referer:
        #     browser.get(referer)
        # scroll()
        WebDriverWait(browser, 10).until(waiter(referer))
        scroll()
        selenium_html = browser.execute_script("return document.documentElement.outerHTML")
        return selenium_html
        # cookie = 'read_mode=day; default_font=font2; locale=zh-CN; _ga=GA1.2.1776733808.1479796358; _gid=GA1.2.898847850.1511762787; Hm_lvt_0c0e9d9b1e7d617b3e6842e85b9fb068=1511495243,1511510502,1511762788,1511832078; Hm_lpvt_0c0e9d9b1e7d617b3e6842e85b9fb068=1511850463; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2215f9ffaadd9d79-0fdd2a85f9cf8c-3b3e5906-2073600-15f9ffaaddab48%22%2C%22%24device_id%22%3A%2215f9ffaadd9d79-0fdd2a85f9cf8c-3b3e5906-2073600-15f9ffaaddab48%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_utm_source%22%3A%22desktop%22%2C%22%24latest_utm_medium%22%3A%22index-users%22%2C%22%24latest_utm_campaign%22%3A%22maleskine%22%2C%22%24latest_utm_content%22%3A%22note%22%7D%7D; _m7e_session=c039f6549f3c11b8f2b1f992da6a1e82'
        #
        # cookie = ('signin_redirect=%s;' % urllib.parse.quote_plus(referer)) + cookie
        # req = urllib.request.Request(request_url)
        # req.add_header('User-Agent',
        #                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        # req.add_header('Accept', 'text/html, */*; q=0.01')
        # # req.add_header('Accept-Encoding', 'gzip, deflate')
        # req.add_header('Accept-Language', 'en')
        # req.add_header('Host', 'www.jianshu.com')
        # req.add_header('If-None-Match', 'W/"59a807c7647a85708e0ff1aac3c42259"')
        # req.add_header('Referer', referer)
        # req.add_header('Cookie', cookie)
        # req.add_header('X-CSRF-Token',
        #                'ANWhDzKxoG57AnMSgRa5Fk+OP4Tswxmb42FkYt6/t6kizZE4UZtNts42zlVRNTXwYcYs/6+31HNBT84ySWP45w==')
        # req.add_header('X-INFINITESCROLL', 'true')
        # req.add_header('X-Requested-With', 'XMLHttpRequest')
        #
        # with urllib.request.urlopen(req) as f:
        #     print(type(f))
        #     print('status: ', f.status, f.reason)
        #     html_text = f.read().decode('utf8', errors='replace')
        #     return html_text
    except Exception as ex:
        raise ex

def waiter(referer):
    if browser.current_url != referer:
        browser.get(referer)

def scroll():
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
    return src_text.replace('📷', ' ')
