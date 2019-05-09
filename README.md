# 迁移Hexo到typecho

这是一个能解析_posts文件夹中的所有符合 `Hexo YAML` 格式的 markdown 文件解析，并且能远程连接 typecho 数据库，导入文章，标签，分类。

## 准备工作

安装 Python3.x，以及依赖 pymysql

```bash
pip3 install pymysql
```



## 使用方法

下载或克隆此项目，打开 `main.py` ，进行编辑，在 `HexoToTypecho(host='', user='', database='', files, passwd='')` （位于最后一行），填入相关参数，分别是 typecho数据库，用户名，数据库名，密码。

默认处理md文件夹位于 `_posts` 文件夹。使用前把 `main.py` 放入 `你的hexo目录/source` 然后使用 Python3 运行。

## 常见问题

* 出现 NoneType 报错
  - 文档没有按照标准 markdown 格式或 YAML 格式编写
* 正文提取出现 NoneType 报错
  - `---`内容后加两个 `\n` 再写正文