import sqlite3
# from flask import jsonify, Flask, current_app
from newspaper import Article
import newspaper
import base64
import io
import urllib
import json
import bcrypt
import matplotlib.pyplot as plt
import numpy as np
import wordcloud
import codecs
from wordcloud import WordCloud, STOPWORDS
import nltk
from nltk.tokenize import word_tokenize
import urllib.request as urllib2
from urllib.request import urlopen


def get_all(sql):
    conn = sqlite3.connect('data/newsdb.db')
    data = conn.execute(sql).fetchall()
    conn.close()
    return data


def count_article_by_category(category_id):
    conn = sqlite3.connect('data/newsdb.db')
    sql = 'SELECT COUNT(id) FROM article WHERE category_id = ?'
    data = conn.execute(sql, (category_id, )).fetchall()
    conn.close()
    return data


def get_all_by_category(category_id, offset):
    conn = sqlite3.connect('data/newsdb.db')
    sql = 'SELECT * FROM article WHERE category_id = ? ORDER BY id DESC LIMIT 20 OFFSET ?'
    data = conn.execute(sql, (category_id, offset, )).fetchall()
    conn.close()
    return data


def get_article_by_id(article_id):
    conn = sqlite3.connect('data/newsdb.db')
    sql = '''
    SELECT A.* FROM
    article A INNER JOIN category C ON A.category_id = C.id
    WHERE A.id = ?
    '''
    data = conn.execute(sql, (article_id,)).fetchone()
    conn.close()

    return data


def get_news_url():
    categories = get_all('SELECT * FROM Category')
    conn = sqlite3.connect('data/newsdb.db')
    for cat in categories:
        cat_id = cat[0]
        cat_url = cat[2]
        cat_paper = newspaper.build(cat_url)
        print('===cat_id: ' + str(cat_id))
        for article in cat_paper.articles:
            try:
                print('===article: ' + article.url)
                add_article(conn, article.url, cat_id)
            except Exception as ex:
                print('ERROR: ' + str(ex))
                pass
    conn.close()


def add_article(conn, url, cat_id):
    sql = '''
    INSERT INTO article(title, description, image_url, original_url, published_date, category_id, content, 
    top_image, authors, tokenizer_content)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    article = Article(url)
    article.download()
    article.parse()
    noun = ['NN', 'NNS', 'NNP', 'NNPS']
    authors = ','.join(article.authors)
    tokenizer_content = word_tokenize(article.text)
    pos_tag_list = nltk.pos_tag(tokenizer_content)
    tmp = []
    for i in pos_tag_list:
        if i[1] in noun:
            tmp.append(i[0])
    word_cloud_content = ' '.join(tmp)
    conn.execute(sql, (article.title, article.meta_description, article.meta_img, article.url, article.publish_date,
                       cat_id, article.text, article.top_image, authors, word_cloud_content))
    conn.commit()


def get_comment(article_id):
    conn = sqlite3.connect('data/newsdb.db')
    sql = 'SELECT * FROM comment WHERE article_id = ? ORDER BY published_Date DESC'
    data = conn.execute(sql, (article_id,)).fetchall()
    conn.close()
    return data


def post_comment(author, body, published_date, article_id):
    conn = sqlite3.connect('data/newsdb.db')
    sql = '''
     INSERT INTO comment(author, body, published_date, article_id)
     VALUES (?, ?, ?, ?)
     '''
    data = conn.execute(sql, (author, body, published_date, article_id,))
    conn.commit()
    if data is not None:
        return True
    return False


def get_trending(offset):
    conn = sqlite3.connect('data/newsdb.db')
    sql = '''
        SELECT tokenizer_content FROM article;
    '''
    rows = conn.execute(sql,)
    sentences = []
    for r in rows:
        sentences.append(r)
    cloud = np.array(sentences).flatten()
    fig = plt.figure(figsize=(30, 20))

    # stop_words = stop_words + list(STOPWORDS)
    stop_words = []
    with codecs.open("StopWord/stopword.txt", 'r', encoding='utf8') as file_in:
        for line in file_in:
            stop_words.append(line.strip())
    for n in stop_words:
        STOPWORDS.add(n)
    word_cloud = wordcloud.WordCloud(stopwords=STOPWORDS, max_words=700,
                                     background_color="white", width=1000, height=400,
                                     mode="RGB").generate(str(cloud)).to_image()
    # convert word-clou image to base64
    img = io.BytesIO()
    word_cloud.save(img, "PNG")
    img.seek(0)
    img_b64 = base64.standard_b64encode(img.getvalue()).decode()
    # Send image to Imgur
    client_id = "3bc58602360427f"
    headers = {'Authorization': 'Client-ID ' + client_id}
    data = {'image': img_b64, 'title': 'word cloud image'}  # create a dictionary.
    main_data = urllib.parse.urlencode(data)
    main_data = main_data.encode('utf-8')
    request = urllib2.Request(url="https://api.imgur.com/3/upload.json", data=main_data, headers=headers)
    response = urlopen(request).read()
    parse = json.loads(response)
    image_url = parse['data']['link']

    t = WordCloud().process_text(str(cloud))
    lst_trending_word = sorted(t.items(), key=lambda x: x[1], reverse=True)

    top10 = lst_trending_word[:10]
    tmp = []
    for i in top10:
        tmp.append(i[0])
    sql2 = '''
        SELECT * FROM article WHERE tokenizer_content LIKE ? ORDER BY id DESC LIMIT 20 OFFSET ?'''
    trending_article = []
    for word in tmp:
        data = conn.execute(sql2, ('%'+word+'%', offset)).fetchall()
        for i in data:
            if i[0] not in trending_article:
                trending_article.append(i)
    conn.close()
    return trending_article, image_url
    # result = []
    # for article in trending_article:
    #     result.append(json_modal(article))
    # return jsonify({'top-trending': result, 'WC_image_url': parse['data']['link']})


if __name__ == '__main__':
    # get_news_url()
    get_trending(10)
    # get_all_by_category(6,20)


# def get_user(email, username):
#     conn = sqlite3.connect('data/newsdb.db')
#     sql = '''
#       SELECT * FROM user WHERE email = ? OR username = ?
#        '''
#     data = conn.execute(sql, (email, username,)).fetchone()
#     conn.commit()
#     return data
#
#
# def check_user(email, username):
#     return get_user(email, username) is not None
#
#
# def create_user(email, username, password):
#     if check_user(email, username):
#         return False
#     conn = sqlite3.connect('data/newsdb.db')
#     hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(9))
#     sql = '''
#      INSERT INTO user(email, username, password)
#      VALUES (?, ?, ?)
#      '''
#     conn.execute(sql, (email, username, hashed_password,))
#     conn.commit()
#     return True
#
#
# def get_user_for_login(username):
#     conn = sqlite3.connect('data/newsdb.db')
#     sql = '''
#           SELECT * FROM user WHERE username = ?
#            '''
#     data = conn.execute(sql, (username,)).fetchone()
#     conn.commit()
#     return data
#
#
# def login(username, password):
#     user = get_user_for_login(username)
#     if user is None:
#         return False
#     return bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8'))