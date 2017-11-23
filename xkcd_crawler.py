# 动漫图片链接抓取并下载
import os

import bs4
import requests
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s -%(message)s')
##logging.basicConfig(filename=r'D:\python test files\firstlog.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s -%(message)s')
##logging.debug('start of program')
def comicPicsCrawling():
    keyWord = ''
    hea = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'}
    baseUrl = 'https://xkcd.com'

    dirname = 'D://Comic Pictures'

    extraTextPath = 'D://Comic Pictures//extra.dat'
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    downloadUrl = baseUrl
    while not downloadUrl.endswith('#'):
        ##        file = open('D://search.dat','a')
        print(downloadUrl)
        urlResponse = requests.get(downloadUrl, headers=hea)
        try:
            urlResponse.raise_for_status()
        except Exception as err:
            logging.error('search failed: ' + str(err))
            logging.debug(str(urlResponse.status_code))
            return
        if urlResponse.status_code == requests.codes.ok:
            soup = bs4.BeautifulSoup(urlResponse.text, "html.parser")
            soup.encode('utf-8')
            elems = soup.select("div#comic img")
            logging.debug('==========select img count: ' + str(len(elems)))
            if len(elems) > 0:
                srcUrl = elems[0].get('src')
                title = elems[0].get('title')
                imgName = os.path.basename(srcUrl)

                imgResponse = requests.get(downloadUrl + srcUrl)
                imgResponse.raise_for_status()

                imgFile = open(os.path.join(dirname, imgName), 'wb')
                for line in imgResponse.iter_content(10000):
                    imgFile.write(line)

                extraFile = open(extraTextPath, 'ab')
                extraFile.write(('========' + imgName + '=======\n').encode('utf-8'))
                extraFile.write((title + '\n\n').encode('utf-8'))
                extraFile.close()

            preElems = soup.select('a[rel="prev"]')
            if len(preElems) > 0:
                downloadUrl = baseUrl + preElems[0].get('href')
            else:
                print('***************previous img is null****************')

def comicPicsCrawling1():
    hea = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'}
    extraTextPath = 'D://Comic Pictures//extra.dat'

    downloadUrl = "https://xkcd.com/1814/"
    urlResponse = requests.get(downloadUrl, headers=hea)
    try:
        urlResponse.raise_for_status()
    except Exception as err:
        logging.error('search failed: ' + str(err))
        logging.debug(str(urlResponse.status_code))
        return
    if urlResponse.status_code == requests.codes.ok:
        soup = bs4.BeautifulSoup(urlResponse.text, "html.parser")
        soup.encode('utf-8')
        elems = soup.select("div#comic img")
        logging.debug('==========select img count: ' + str(len(elems)))
        if len(elems) > 0:
            srcUrl = elems[0].get('src')
            title = elems[0].get('title')
            imgName = os.path.basename(srcUrl)

            print(title)
            print(type(elems[0]))
            try:
                extraFile = open(extraTextPath, 'a')
                extraFile.write('========' + imgName + '=======\n')
                extraFile.write(title + '\n\n')
                extraFile.close()
            except:
                extraFile = open(extraTextPath, 'ab')
                extraFile.write(('========' + imgName + '=======\n').encode('utf-8'))
                extraFile.write((title + '\n\n').encode('utf-8'))
                extraFile.close()