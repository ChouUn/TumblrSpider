
import sqlite3
conn = sqlite3.connect('data.db')

c = conn.cursor()
c.execute('''CREATE TABLE records
             (id TEXT PRIMARY KEY, blog TEXT, src TEXT, dir TEXT, name TEXT, downloaded BOOLEAN)''')
c.execute('''CREATE TABLE errors
             (id TEXT, blog TEXT, post TEXT, exc TEXT)''')
c.execute('''CREATE INDEX src_index ON records(src)''')

conn.commit()
conn.close()