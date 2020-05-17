import requests,os,json
from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from tqdm import tqdm



COURSE_URL = 'https://academy.moz.com/seo-fundamentals'




def getVideo(soup):
    videoTag = soup.find(attrs={'name':'wistia_embed'})['src'].split('?')[0].split('/')[-1]
    jsonUrl = f"https://fast.wistia.com/embed/medias/{videoTag}.json"
    r = requests.get(jsonUrl)
    jsonData = r.json()
    video = jsonData['media']['assets'][0]
    videoExt = video.get('ext','mp4')
    videoUrl = video['url']
    videoName = jsonData['media']['name'].replace('?','')
    return videoUrl,videoName,videoExt

def getCookies():
    j = json.load(open("cookies.json"))
    cookies = {}
    for cookie in j:
        cookies[cookie['name']] = cookie['value']
    return cookies

def download_file(url,name):
    local_filename = name
    headers = {}
    if os.path.exists(local_filename):
        headers = {'Range': 'bytes=%d-' % (os.path.getsize(local_filename))}
        print("\t\t[>] Resuming Video")
    with requests.get(url, stream=True,headers=headers) as r:
        if not r and headers:
            print("\t\t[+] Video Already Downloaded")
            return
        total_size = int(r.headers.get('content-length', 0))
        t=tqdm(total=total_size, unit='iB', unit_scale=True)
        r.raise_for_status()
        with open(local_filename, 'ab') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                t.update(len(chunk))
                if chunk: 
                    f.write(chunk)
        t.close()
        if total_size != 0 and t.n != total_size:
            print("\t\tERROR, something went wrong")

headers = {
    'authority': 'academy.moz.com',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'referer': 'https://academy.moz.com/',
    'accept-language': 'en-US,en;q=0.9',
}
cookies = getCookies()
main = "https://academy.moz.com"
response = requests.get(COURSE_URL,cookies=cookies, headers=headers)
soup = bs(response.text,'lxml')
courseName = soup.find('h1',class_='break-word').get_text(strip=True)
if not os.path.exists(courseName):
    os.mkdir(courseName)
chapters = []
topics = []
chapters.append(soup.find(class_='content').h2.get_text("|||",True).split('|||')[0])
for tag in soup.findAll('a',class_='lesson-template-video-wistia'):
    tags = [a for a in tag.previous_siblings if type(a)==Tag]
    if tags and tags[0].name=='div':
        chapters.append(tags[0].get_text(strip=True).replace('?',''))
    tag.find(class_='sj-lesson-time').extract()
    topics.append((chapters[-1],main+tag['href'],tag.get_text(strip=True).replace('?','')))
print("[+] Course:",courseName)
for topic in topics:
    url = topic[1]
    topicTitle = topic[2]
    chapter = topic[0]
    if not os.path.exists(os.path.join(courseName,chapter)):
        os.mkdir(os.path.join(courseName,chapter))
    if chapter in chapters:
        print("\t[+] Topic:",chapter)
        chapters.pop(chapters.index(chapter))
    soup = bs(requests.get(url,headers=headers,cookies=cookies).text,'lxml')
    videoUrl,videoName,videoExt = getVideo(soup)
    print("\t\t[+] Video:",topicTitle)
    download_file(videoUrl,os.path.join(courseName,chapter,videoName+'.'+videoExt))
print("[+] Completed")