import re
import pymysql
import time
import os


class HexoToTypecho():
    def __init__(self, host, user, database, files, passwd=''):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = 3306
        self.database = database
        self.files = files
        # self.parse_hexo_md()
        for i in files:
            self.insert_post(i)
            self.insert_tags_category()
            self.relationships()
        self.db.close()

    def connectSQL(self):
        sql = pymysql.connect(host=self.host, user=self.user, password=self.passwd, database=self.database,
                              charset='utf8')
        return sql.cursor(), sql

    def parse_hexo_md(self,file):
        # TODO 文件名可以作为缩略名
        with open('_post/'+file, encoding='utf-8') as f:
            s = f.read()
            print('当前处理 --->  ', file)

        # 标题提取
        title = re.search(r'title: (.*?)\n', s, re.S).group(1)
        # 时间转化时间截
        date = re.search(r'date: (.*?)\n', s, re.S).group(1)
        date = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        date = int(time.mktime(date))

        if not re.search(r'tags: (.*?)\n', s):
            items = re.search(r'tags:\n(.*?)\nca', s, re.S).group(1)
            tags = re.findall(r'- (.*?)\n', items)
        else:
            tags = re.search(r'tags: (.*?)\n', s).group(1)

        if not re.search(r'categories: ', s):
            items = re.search(r'categories:\n(.*?)\n---', s, re.S).group(1)
            categories = re.findall('- (.*?)\\n', items)
        else:
            categories = re.search(r'categories: (.*?)\n', s).group(1)
        # 正文提取
        post = re.search(r'---\n\n(.*?)$', s, re.S).group(1)

        # print((title, date, tags, categories,post))
        return (title, date, tags, categories, '<!--markdown-->' + post)

    def insert_post(self,file):
        data = self.parse_hexo_md(file)
        self.data = data
        cur, db = self.connectSQL()
        self.db = db
        self.cur = cur
        sql = '''
        INSERT INTO typecho_contents(title,slug, created,modified, text,type,status,allowcomment,allowfeed,authorid) VALUES (%s,%s,%s,%s,%s,'post','publish',1,1,1) 
        '''

        try:
            cur.execute(sql, (data[0], file, data[1], data[1], data[4]))
            db.commit()
        except Exception as e:
            print(e)
            db.rollback()

    def insert_tags_category(self):
        data = self.data
        cur = self.cur
        cur.execute('ALTER TABLE typecho_metas ADD UNIQUE KEY(name,type)')
        sql = '''
        INSERT INTO typecho_metas(name,slug,type) VALUES (%s,%s,'tag') ON DUPLICATE KEY UPDATE count = count + 1
        '''
        # tags导入
        try:
            # (title, date, tags, categories, '<!--markdown-->' + post)
            if isinstance(data[2], list):
                for i in data[2]:
                    cur.execute(sql, (i, i))
                    self.db.commit()
            else:
                cur.execute(sql, (data[2], data[2]))
                self.db.commit()
        except pymysql.DatabaseError as e:
            print(e)
            self.db.rollback()

        # category 导入
        sql = '''
                INSERT INTO typecho_metas(name,slug,type) VALUES (%s,%s,'category') ON DUPLICATE KEY UPDATE count = count + 1
              '''
        try:
            # (title, date, tags, categories, '<!--markdown-->' + post)
            if isinstance(data[3], list):
                for i in data[3]:
                    cur.execute(sql, (i, i))
                    self.db.commit()
            else:
                cur.execute(sql, (data[3], data[3]))
                self.db.commit()
        except pymysql.DatabaseError as e:
            print(e)
            self.db.rollback()

    def relationships(self):
        db = self.db
        cur = self.cur
        data = self.data

        # 映射 tags
        select_mid = '''
                SELECT mid FROM typecho_metas WHERE name = %s AND type = %s
            '''
        select_cid = '''
                        SELECT cid FROM typecho_contents WHERE title = %s
                    '''
        add_relationship = '''
                INSERT INTO typecho_relationships(cid,mid) VALUES (%s,%s)
        '''

        try:
            cur.execute(select_cid, (data[0]))
            
            cid = cur.fetchall()[0][0]  # 获取 cid

            if isinstance(data[2], list):
                for i in data[2]:
                    cur.execute(select_mid, (i, 'tag'))
                    tu = cur.fetchall()
                    # print('mid = ', tu[0][0])  # mid 获取
                    mid = tu[0][0]

                    cur.execute(add_relationship, (cid, mid))
            else:
                cur.execute(select_mid, (data[2], 'tag'))
                tu = cur.fetchall()
                # print('mid = ', tu[0][0])  # mid 获取
                mid = tu[0][0]
                cur.execute(add_relationship, (cid, mid))
        except pymysql.DatabaseError as e:
            print(e)
            db.rollback()

        # categories
        # (title, date, tags, categories, '<!--markdown-->' + post)
        try:
            if isinstance(data[3], list):
                for i in data[3]:
                    cur.execute(select_mid, (i, 'category'))
                    tu = cur.fetchall()
                    # print('mid = ', tu[0][0])  # mid 获取
                    mid = tu[0][0]

                    cur.execute(add_relationship, (cid, mid))
            else:
                cur.execute(select_mid, (data[3], 'category'))
                tu = cur.fetchall()
                # print(tu)  # mid 获取
                mid = tu[0][0]
                cur.execute(add_relationship, (cid, mid))
        except pymysql.DatabaseError as e:
            print(e)
            db.rollback()


if __name__ == '__main__':
    files = [f for f in os.listdir('_post') if not f.startswith('.')]
    print('总有', files)
    HexoToTypecho(host='', user='', database='', files='', passwd='')
