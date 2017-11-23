import logging
import sys
import bs4
import requests

def googleWebCrawling():
    keyWord = ''
    if len(sys.argv) > 1:
        keyWord = sys.argv[1]
    if keyWord == None or keyWord == '':
        keyWord = '电影'

    hea = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'
        , 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'referer': 'https://www.google.com.tw/',
        'upgrade-insecure-requests': '1'}
    firstUrl = 'http://www.google.com.tw/search?q=%s&oq=%s'
    otherUrl = 'http://www.google.com.tw/search?q=%s&oq=%s&start=%d'
    pageIndex = 0
    searchNoneCount = 0
    i = 1
    while pageIndex < 100:
        url = firstUrl % (keyWord, keyWord)
        if pageIndex != 0:
            url = otherUrl % (keyWord, keyWord, pageIndex * 10)
        print(url)
        urlResponse = requests.get(url, headers=hea)
        try:
            urlResponse.raise_for_status()
        except Exception as err:
            logging.error('search failed: ' + str(err))
            logging.debug(str(urlResponse.status_code))
            return
        if urlResponse.status_code == requests.codes.ok:
            # logging.info(urlResponse.text)
            soup = bs4.BeautifulSoup(urlResponse.text, "html.parser")
            elems = soup.select("div#rso")
            logging.debug('==========select element count: ' + str(len(elems)))
            # print(str(elems[0]))
            if len(elems) > 0:
                childSoup = bs4.BeautifulSoup(str(elems[0]), "html.parser")
                childElems = childSoup.select('h3.r a')
                logging.debug('select child element count: ' + str(len(childElems)))
                for child in childElems:
                    print('******' + str(child))
                    childUrl = child.get('href')
                    childname = child.string
                    print('[%d] %s : %s ' % (i, childname, childUrl))
                    i += 1
            else:
                searchNoneCount += 1
                if searchNoneCount > 5:
                    break
        pageIndex += 1
