
import os
import shutil
import sqlite3
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import PurePath

WORKERS = 10
PAGE_SIZE = 1000
DOWN_DIR = './downloads'

def get_file(task):
    file_id, file_blog, file_src, file_dir, file_name, downloaded = task

    real_dir = str(PurePath(DOWN_DIR, file_dir))
    real_name = str(PurePath(DOWN_DIR, file_dir, file_name))

    if not os.path.exists(real_dir):
        try:
          os.makedirs(real_dir)
        except Exception as exc:
          print('WARNING: %r generated an exception: %s' % (file_id, exc))
    if os.path.exists(real_name):
        return

    with urllib.request.urlopen(file_src) as response, open(real_name, 'w+b') as out_file:
        shutil.copyfileobj(response, out_file)

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('UPDATE records SET downloaded = 1 WHERE id = ?', (file_id, ))
    conn.commit()
    conn.close()

if __name__=='__main__':
    if len(sys.argv) == 2:
        WORKERS = int(sys.argv[1])
        print('CONFIG: set WORKERS to %d (default 10)' % (WORKERS, ))

    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    c.execute('SELECT count(*) FROM records')
    total = c.fetchone()[0]
    page = (total + PAGE_SIZE - 1) // PAGE_SIZE

    for i in range(page):
        c.execute('''
            SELECT *
            FROM records AS A
            WHERE 
                id in (
                    SELECT id 
                    FROM records
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                ) AND 
                src not in (
                    SELECT src
                    FROM records AS B
                    WHERE B.id < A.id
                    ORDER BY id ASC
                ) AND
                downloaded = 0
        ''', (PAGE_SIZE, i * PAGE_SIZE))
        tasks = c.fetchall()

        with ThreadPoolExecutor(max_workers=WORKERS) as e:
            future_to_url = { e.submit(get_file, task): task for task in tasks }
            for future in as_completed(future_to_url):
                task = future_to_url[future]
                try:
                    future.result()
                except Exception as exc:
                    print('ERROR: %r generated an exception: %s' % (task[0], exc))
            print('%d items are checked.' % ((i + 1) * PAGE_SIZE))
