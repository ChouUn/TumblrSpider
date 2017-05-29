
import re
import sqlite3
import sys
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from lxml import etree

# PROXIES = { 
#     "http": "socks5://127.0.0.1:1080",
# }
WORKERS = 5
TEST_SIZE = 0
PAGE_SIZE = 50
TEST_URl = 'http://%s.tumblr.com/api/read?&num=%d'
BLOG_URL = 'http://%s.tumblr.com/api/read?&num=%d&start=%d'

def get_url(url):
    # req = requests.get(url, allow_redirects=True, proxies=PROXIES)
    req = requests.get(url, allow_redirects=True)
    if req.status_code == 404: return None
    return req.content

def element_tostring(element):
    return etree.tostring(element, pretty_print=True).decode(encoding="UTF-8")

def get_all_posts(queue, blog):
    raw = get_url(TEST_URl % (blog, TEST_SIZE))
    if raw == None: return
    xml = etree.XML(raw)
    totals = xml.xpath('/tumblr/posts[1]/@total')
    total = int(totals[0])
    element_tostring(xml)

    page = (total + PAGE_SIZE - 1) // PAGE_SIZE
    # page = 1
    for i in range(page):
        blog_req = BLOG_URL % (blog, PAGE_SIZE, i * PAGE_SIZE)
        queue.append(blog_req)

def load_url(blog, url, timeout):
    raw = get_url(url)
    if raw == None: return
    xml = etree.fromstring(raw)
    posts = xml.xpath('/tumblr/posts/post')
    if len(posts) != PAGE_SIZE:
        print('WARNING: page size is %d, but the real is %d' % (PAGE_SIZE, len(posts)))
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    for post in posts:
        media_id = post.xpath('@id')[0]
        media_type = post.xpath('@type')[0]
        media_dir = './%s/%s' %(blog, media_type)

        if media_type == 'video':
            try:
                video_raw = post.xpath('video-player')[0].text
                video_match = re.search(r'<source src="(.*)" type="(.*)">', video_raw)
                video_src, video_type = video_match.groups()
                video_name = video_src.split('/')[-1]
                video_ext = video_type.split('/')[-1]

                media_name = media_id + '.' + video_ext 
                c.execute('SELECT * FROM records WHERE id = ?', (media_id, ))
                if c.fetchone() == None:
                    c.execute('INSERT INTO records VALUES (?, ?, ?, ?, ?, ?)', (media_id, blog, video_src, media_dir, media_name, False))
            except Exception as exc:
                c.execute('INSERT INTO errors VALUES (?, ?, ?, ?)', (media_id, blog, element_tostring(post), str(exc)))
        elif media_type == 'photo':
            if len(post.xpath('photoset')) > 0:
                photos = post.xpath('photoset/photo/photo-url[@max-width="1280"]')
            else:
                photos = post.xpath('photo-url[@max-width="1280"]')
            for photo in photos:
                try:
                    photo_src = photo.text
                    photo_full_name = photo_src.split('/')[-1]
                    photo_ext = photo_full_name.split('.')[-1]

                    media_name = media_id + '.' + photo_ext
                    c.execute('SELECT * FROM records WHERE id=?', (media_id, ))
                    if c.fetchone() == None:
                        c.execute('INSERT INTO records VALUES (?, ?, ?, ?, ?, ?)', (media_id, blog, photo_src, media_dir, media_name, False))
                except Exception as exc:
                    c.execute('INSERT INTO errors VALUES (?, ?, ?, ?)', (media_id, blog, element_tostring(post), str(exc)))
    conn.commit()
    conn.close()

def unique_list(seq): # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

if __name__=='__main__':
    if len(sys.argv) == 2:
        WORKERS = int(sys.argv[1])
        print('CONFIG: set WORKERS to %d (default 5)' % (WORKERS, ))

    blogs = []
    with open('source.txt', 'r') as in_file:
        blogs = [line.strip() for line in in_file.readlines()]
        blogs = unique_list(list(filter(lambda blog: blog != '', blogs)))

    for i in range(len(blogs)):
        blog = blogs[0]
        queue = deque([])
        get_all_posts(queue, blog)

        with ThreadPoolExecutor(max_workers=WORKERS) as e:
            future_to_url = { e.submit(load_url, blog, url, 60): url for url in queue }
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()
                    print('%r success' % (url))
                except Exception as exc:
                    print('ERROR: %r generated an exception: %s' % (url, exc))
        
        blogs = blogs[1:] + blogs[0:1]
        with open('source.txt', 'w') as out_file:
            for blog in blogs:
                out_file.write(blog + '\n')
