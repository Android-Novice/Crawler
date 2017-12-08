#!python3
# --*-- coding: utf-8 --*--
import random
import sys
import urllib
from multiprocessing.pool import Pool
import logging
import bs4
import re
import os
import requests
import time

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s -%(message)s')
##logging.basicConfig(filename=r'D:\python test files\firstlog.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s -%(message)s')
##logging.debug('start of program')

visited_urls = ['http://www.baidu.com', 'www.baidu.com', 'http://www.baidu.com/']

def baiduWebCrawling(keyWord=''):
    if len(sys.argv) > 1:
        keyWord = sys.argv[1]
    if keyWord == None or keyWord == '':
        keyWord = '淘宝模特'

    global _pool
    _pool = Pool(4)

    # base_url = 'https://www.baidu.com/s'
    firstUrl = 'https://www.baidu.com/s?wd=%s&oq=%s'
    otherUrl = 'https://www.baidu.com/s?wd=%s&pn=%d&oq=%s'
    pageIndex = 0
    searchNoneCount = 0
    i = 1
    file = open('D://search.dat', 'ab')
    file.write(('==================' + keyWord + '==================\n').encode('utf-8'))
    file.close()
    # params = {'wd': keyWord, 'oq': keyWord}
    urls = []
    while pageIndex < 1:
        print('#############################################1')
        file = open('D://search.dat', 'ab')
        url = firstUrl % (keyWord, keyWord)
        if pageIndex != 0:
            url = otherUrl % (keyWord, pageIndex * 10, keyWord)
        print(url)

        soup, urlResponse = get_beautifulsoup(url)
        print('#############################################2')
        if soup != None:
            elems = soup.select("div#content_left")
            logging.debug('==========select element count: ' + str(len(elems)))
            # print(str(elems[0]))
            print('#############################################3')
            if len(elems) > 0:
                childSoup = bs4.BeautifulSoup(str(elems[0]), "html.parser")
                childElems = childSoup.select('h3.t a')
                print('#############################################4')
                logging.debug('select child element count: ' + str(len(childElems)))
                for child in childElems:
                    print('#############################################5')
                    print('******' + str(child))
                    childUrl = child.get('href')
                    childUrl = getDirectUrl(childUrl)
                    if (not (childUrl is None)) and childUrl not in urls:
                        urls.append(childUrl)
                    childname = child.text
                    info = '[%d] %s : %s\n' % (i, childname, childUrl)
                    print(info)
                    i += 1
                    file.write(info.encode('utf-8'))
                    print('#############################################6')
            else:
                searchNoneCount += 1
                if searchNoneCount > 5:
                    break
        file.close()
        time.sleep(random.randint(1, 5))
        pageIndex += 1
        print('#############################################7')

    while len(urls) > 0:
        print('#############################################8')
        urls = get_all_image_video(urls)
        print('#############################################9')

def get_all_image_video(urls):
    global visited_urls
    web_urls = []
    index = 1
    for url in urls:
        if url in visited_urls:
            continue
        visited_urls.append(url)
        print('#############################################11')
        soup, urlResponse = get_beautifulsoup(url)
        if soup != None:
            elems = soup.select('img')
            logging.info(str(len(elems)))
            print('#############################################12')
            if len(elems) > 0:
                for elem in elems:
                    try:
                        print('#############################################13')
                        imgUrl = elem.get('data-original')
                        if imgUrl == None:
                            imgUrl = elem.get('data-actualsrc')
                            if imgUrl == None:
                                imgUrl = elem.get('data-src')
                                if imgUrl == None:
                                    imgUrl = elem.get("src")
                        print(imgUrl)
                        imgUrl = filter_url(imgUrl, urlResponse)
                        if imgUrl != None and imgUrl not in visited_urls:
                            visited_urls.append(imgUrl)
                            _pool.apply_async(download_image, args=((imgUrl, index)))
                            print('#############################################14')
                        index += 1
                    except Exception as error:
                        logging.error(str(error))
            print('#############################################15')
            urlElems = soup.select('body a')
            if len(urlElems) > 0:
                for item in urlElems:
                    url = item.get('data-href')
                    if url == None:
                        url = item.get('href')
                    url = filter_url(url, urlResponse)
                    if url != None and (url not in visited_urls and url not in web_urls):
                        web_urls.append(url)
            print('#############################################16')
    return web_urls

def download_image(url, index):
    print('#############################################31')
    extension = ''
    try:
        splits = os.path.splitext(url)
        extension = splits[1]
        if extension == '':
            extension = '.jpg'
    except Exception as error:
        logging(str(error))
    root_dir = 'D://download images'
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
    path = os.path.join(root_dir, str(index) + extension)
    try:
        logging.info(url + ' =====> ' + path)
        print(url + ' =====> ' + path)
        # urllib.request.urlretrieve(url, path)
        hea = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Cookie': ''
        }
        print('#############################################32')
        imgResponse = requests.get(url, hea)
        print('**************************Code: ' + str(imgResponse.status_code))
        imgResponse.raise_for_status()
        if imgResponse.status_code == 200:
            if str(imgResponse.headers.get('content-length')) == '5484':
                print('-----------------******-----------------')
                return
            print('#############################################33')
            imgFile = open(path, 'wb')
            for line in imgResponse.iter_content(100000):
                imgFile.write(line)
            imgFile.close()
            print('#############################################34')
    except Exception as error:
        logging.error(str(error))

def filter_url(url, response):
    if url == None or url == '/' or url == '':
        return None
    if url.startswith('//'):
        url = 'http:' + url
    elif not url.startswith('http'):
        proto, rest = urllib.request.splittype(response.url)
        host, rest = urllib.request.splithost(rest)
        if host != None:
            url = host + url
            if not url.startswith('http'):
                url = 'http://' + url
        else:
            return None
    return url

def get_beautifulsoup(url, params):
    hea = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'}
    logging.info('************************************************')
    logging.info('start url:' + url)
    try:
        print('#############################################21')
        urlResponse = requests.get(url, headers=hea)
        urlResponse.raise_for_status()
        if urlResponse.status_code == requests.codes.ok:
            soup = bs4.BeautifulSoup(urlResponse.text, "html.parser")
            print('#############################################22')
            return soup, urlResponse
    except Exception as err:
        logging.error('search failed: ' + str(err))
    return None, None

def getDirectUrl(redirectUrl):
    try:
        tmpPage = requests.get(redirectUrl, allow_redirects=False)
        if tmpPage.status_code == requests.codes.ok:
            ##此处代码有待验证，目前还没有进到这个里面，应该有问题；
            pageText = tmpPage.text.encode('utf-8')
            urlMatch = re.search(r'URL=\'(.*?)\'', tmpPage.text.encode('utf-8'), re.S)
            raise Exception('活捉验证码200的网页一个: ' + redirectUrl)
            return urlMatch.group(1)
            print(pageText)
        elif tmpPage.status_code == 302:
            directUrl = tmpPage.headers.get('location')
            print(directUrl)
            return directUrl
        return redirectUrl
    except Exception as error:
        print('********getDirectUrl error: ' + str(error))
    return None
