import bs4
import requests
import logging

def kuwoWebCrawling():
    mainUrl = 'http://www.kuwo.cn/bang/index'
    urlResponse = requests.get(mainUrl)
    try:
        urlResponse.raise_for_status()
    except Exception as err:
        logging.error('search failed: ' + str(err))
        return
    if urlResponse.status_code == requests.codes.ok:
        ##        logging.debug(urlResponse.text)
        # 下面这一行很重要
        urlResponse.encoding = 'unicode'
        htmlFile = open(r'D:\python test files\html.dat', 'wb')
        for line in urlResponse.iter_content(100000):
            htmlFile.write(line)
        soup = bs4.BeautifulSoup(urlResponse.text, "html.parser")
        elems = soup.select('li')
        logging.debug('select element count: ' + str(len(elems)))
        count = 1
        for elem in elems:
            if parseMusicInfo(str(elem), count):
                count += 1

def parseMusicInfo(musicHtmlText, count):
    url = ''
    name = ''
    artist = ''
    soup = bs4.BeautifulSoup(musicHtmlText, "html.parser")

    nameElems = soup.select('.name a')
    if len(nameElems) > 0:
        name = nameElems[0].string
        url = nameElems[0].get('href')

        artistElems = soup.select('.artist a')
        if len(artistElems) > 0:
            artist = artistElems[0].string
    if url != '' and name != '' and artist != '':
        print('[%d] %s - %s : %s' % (count, artist, name, url))
        return True
    return False
