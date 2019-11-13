import requests
from requests.adapters import HTTPAdapter
import bs4
import re
import json
import time
import os
from sys import argv

session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=3))
session.mount('https://', HTTPAdapter(max_retries=3))

dirPath = './downloads/%s' % argv[1]
filePath = dirPath + '/mp4_info.txt'
startUrl = argv[2]


baseUrl = 'http://www.ksyt.com.cn'
regVid = re.compile(r'videoDetail\.php\?vid="\+\'(.*?)\',')
regNoLogin = re.compile(r'videoDetail\.php\?vid="\+\'(.*?)\',')

headers = {
    "Cookie": "p_h5_u=D0013012-769B-4785-A870-A7AA780160DC; selectedStreamLevel=FD; NTKF_T2D_CLIENTID=guest6099673B-431E-56ED-8497-ED3EB50FA2C6; nTalk_CACHE_DATA={uid:kf_10090_ISME9754_guest6099673B-431E-56,tid:1571643372814903}; PHPSESSID=mfqoto7apo8ditiqnkjirrh475; Hm_lvt_201aceeb853e531973356921f8cd26d5=1571643352,1572340675; PHPSESSID__ckMd5=70eac7e8ab9a95c0; OrdersId=U0JUAAwyBGcBZgVhAjYPNl4%2BAGNRYwQxVAVRGlU0VTFdOA%3D%3D; Hm_lpvt_201aceeb853e531973356921f8cd26d5=1572390926; DedeUserID=12143; DedeUserID__ckMd5=75caaf67d898091b; DedeLoginTime=1572391089; DedeLoginTime__ckMd5=80b37d381d88c00"
}


def getUrl(path):
    return baseUrl + path


def getHtmlText(url):
    try:
        r = session.get(url, timeout=20, headers=headers)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return ""

def getMp4Info(html, mp4Info):
    vid = regVid.search(html)
    if vid:
        jsonUrl = getUrl('/alivod/videoDetail.php')
        try:
            r = session.get(jsonUrl, timeout=20, headers=headers, params={
                'vid': vid.group(1)
            })
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            res = json.loads(r.text)
            for item in res['PlayInfoList']['PlayInfo']:
                if item['Definition'] == 'LD' and item['Format'] == 'mp4': 
                    mp4Info['url'] = item['PlayURL']

            title = res['VideoBase']['Title']
            if title.endswith('_0'):
                title = title[:-2]
            mp4Info['title'] = title
            mp4Info['duration'] = res['VideoBase']['Duration']
        except requests.exceptions.RequestException as e:
            mp4Info['error'] = 'warning1 获取 mp4 URL 失败'
            print(e)
    else:
        mp4Info['error'] = 'warning1 获取 vid 失败'



def getUrlList2(html):
    urlList = []
    soup = bs4.BeautifulSoup(html, "html.parser")
    tagDiv = soup.find('div', id='nks1')
    if tagDiv:
        for tagLi in tagDiv.ul.children:
            if type(tagLi) == bs4.element.Tag:
                pUrl = getUrl( '/home/' + tagLi.a.attrs['href'] )
                urlList.append(pUrl)
    return urlList

def getUrlList(html):
    urlList = []
    regHref = re.compile(r'<a class="vlink" href="(.*?)" title') 
    for href in regHref.finditer(html):
        pUrl = getUrl( '/home/' + href.group(1) )
        urlList.append(pUrl)
    return urlList


def main():
    start = time.time()
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    if os.path.exists(filePath):
        os.remove(filePath)
    # 获取网页结构
    html = getHtmlText(startUrl)
    # 从网页结构中分离出子url列表
    lessonUrlList = getUrlList2(html)
    # 获取子 网页结构
    # 发起 get 请求，得到 mp4 地址
    with open(filePath, 'a', encoding='utf-8') as f:
        a = 0
        for lessonUrl in lessonUrlList:
            # if a == 2:
            #     break
            a = a + 1
            subHtml = getHtmlText(lessonUrl)
            mp4Info = {}
            # mp4Info['id'] = a
            mp4Info['pageUrl'] = lessonUrl
            getMp4Info(subHtml, mp4Info)
            print('获取 {%s} 完成' % mp4Info['title'])
            # mp4InfoList.append(mp4Info)
            # 保存到文件中
            f.write(mp4Info['url'] + '\n')
            f.write( '  out=%02d-%s.mp4\n' % (a, mp4Info['title']) )

    # jsonStr = json.dumps(mp4InfoList, ensure_ascii=False)
    # writeToFile( jsonStr )
    end = time.time()
    print( '本页面 mp4 地址收集完毕, 用时 %s' % str(end-start) )

main()
