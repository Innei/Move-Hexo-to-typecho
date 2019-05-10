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
        self.connectSQL()
        # self.parse_hexo_md()
        for i in files:
            self.insert_post(i)
            self.insert_tags_category()
            self.relationships()
        self.cur.execute(
            'ALTER TABLE typecho_relationships DROP PRIMARY KEY')
        self.db.close()

    def connectSQL(self):
        try:
            sql = pymysql.connect(host=self.host, user=self.user, password=self.passwd, database=self.database,
                                  charset='utf8')
        except pymysql.Error as e:
            print(e)
            quit(1)
        else:
            print('连接成功')
            self.cur = sql.cursor()
            self.db = sql
            self.cur.execute('ALTER TABLE typecho_metas ADD UNIQUE KEY(name,type)')

    def parse_hexo_md(self, file):
        # TODO 文件名可以作为缩略名
        with open('_posts/' + file, encoding='utf-8') as f:
            s = f.read()
            print('当前处理 --->  ', file)

        # 标题提取
        title = re.search(r'title: (.*?)\n', s, re.S).group(1)
        # 时间转化时间截
        date = re.search(r'date: (.*?)\n', s, re.S).group(1)
        date = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        date = int(time.mktime(date))
        try:
            if not re.search(r'tags:[ ]*(.*?)\n', s).group(1):
                if re.search(r'tags:[ ]*\n(.*?)\nca', s, re.S):
                    items = re.search(r'tags:[ ]*\n(.*?)\nca', s, re.S).group(1)
                    tags = re.findall(r'- (.*?)\n', items)
                else:
                    tags = ''
            else:
                tags = re.search(r'tags:[ ]*(.*?)\n', s).group(1)
        except AttributeError as e:
            print(e)
            tags = ''

        try:
            if not re.search(r'categories:[ ]*(.*?)\n', s).group(1):
                if re.search(r'categories:[ ]*\n(.*?)\n---', s, re.S):
                    items = re.search(r'categories:[ ]*\n(.*?)\n---', s, re.S).group(1)
                    categories = re.findall(r'- (.*?)\n', items)
                else:
                    categories = ''
            else:
                categories = re.search(r'categories:[ ]*(.*?)\n', s).group(1)
        except AttributeError as e:
            print(e)
            categories = ''
        # 正文提取
        post = re.search(r'---\n\n(.*?)$', s, re.S).group(1)

        # print((title, date, tags, categories,post))
        return (title, date, tags, categories, '<!--markdown-->' + post)

    def insert_post(self, file):
        data = self.parse_hexo_md(file)
        self.data = data
        db = self.db
        cur = self.cur
        modified = int(time.mktime(time.localtime(os.stat('_posts/' + file).st_mtime)))
        sql = '''
        INSERT INTO typecho_contents(title,slug, created,modified, text,type,status,allowComment,allowFeed,allowPing,authorId) VALUES (%s,%s,%s,%s,%s,'post','publish',1,1,1,1) 
        '''

        try:
            cur.execute(sql, (data[0], file.split('.md')[0], data[1], modified, data[4]))
            db.commit()
        except Exception as e:
            print(e)
            db.rollback()

    def insert_tags_category(self):
        data = self.data
        cur = self.cur
        # cur.execute('ALTER TABLE typecho_metas ADD UNIQUE KEY(name,type)')
        sql = '''
        INSERT INTO typecho_metas(name,slug,type,count) VALUES (%s,%s,'tag',1) ON DUPLICATE KEY UPDATE count = count + 1
        '''
        # tags导入
        try:
            # (title, date, tags, categories, '<!--markdown-->' + post)
            if isinstance(data[2], list):
                for i in data[2]:
                    cur.execute(sql, (i, i))
                    self.db.commit()
            else:
                if data[2]:
                    cur.execute(sql, (data[2], data[2]))
                    self.db.commit()
        except pymysql.DatabaseError as e:
            print(e)
            self.db.rollback()

        # category 导入
        sql = '''
                INSERT INTO typecho_metas(name,slug,type,count) VALUES (%s,%s,'category',1) ON DUPLICATE KEY UPDATE count = count + 1
              '''
        try:
            # (title, date, tags, categories, '<!--markdown-->' + post)
            if isinstance(data[3], list):
                for i in data[3]:
                    cur.execute(sql, (i, i))
                    self.db.commit()
            else:
                if data[3]:
                    cur.execute(sql, (data[3], data[3]))
                    self.db.commit()
        except pymysql.DatabaseError as e:
            print(e)
            self.db.rollback()

    def relationships(self):
        db = self.db
        cur = self.cur
        data = self.data
        print('tag = ', data[2], 'type = ', type(data[2]), 'cet = ', data[3])
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
                print('mid = ', tu)  # mid 获取
                mid = tu[0][0]
                cur.execute(add_relationship, (cid, mid))
        except pymysql.DatabaseError as e:
            print(e)
            db.rollback()
        except IndexError as e:
            print('不能建立关系', data[2])
            return

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
        except IndexError as e:
            print('不能建立关系', data[3])
            return


if __name__ == '__main__':
    files = [f for f in os.listdir('_posts') if not f.startswith('.')]
    print('总有', files)
    HexoToTypecho(host='', user='', database='', files='', passwd='')
