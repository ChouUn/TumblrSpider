
# 汤很热

一个汤不热的爬虫

## 环境

使用 Python 3:  
`pip install -r requirements.txt`

若系统默认 Python 2，请使用以下命令：
`python -m pip install -r requirements.txt`

## 初始化数据库

`python build.py`

## 添加来源

在爬虫没启动时，添加进 `source.txt`。  
位于前面的会优先被爬取，可以自行调整顺序。

## 爬取数据

`python update.py`

`python update.py 10` 开 10 个奴隶

## 下载爬取的 url (TODO)

`python upgrade.py`

`python upgrade.py 20` 开 20 个奴隶

## 查看数据库

### Windows

`sqlite3.exe data.db`

## TODO LIST

- [x] 爬取 photo 和 video 的 url
- [x] 下载已爬取的 url
- [ ] 剔除重复 post（或追踪到原 post）
- [ ] 统计欢迎度（thanks to [watsy0007](https://github.com/watsy0007)）
- [ ] 搞个 ORM 框架，解决下数据库锁的问题