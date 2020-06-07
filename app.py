from flask import Flask, jsonify, request
import utils

app = Flask(__name__)


def json_modal(r):
    return {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "image_url": r[3],
            "original_url": r[4],
            "published_date": r[5],
            "category_id": r[6],
            "content": r[7],
            "top_image": r[8],
            "authors": r[9]
        }


@app.route('/categories', methods=['GET'])
def get_categories():
    sql = 'SELECT * FROM Category'
    rows = utils.get_all(sql)
    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "name": r[1],
            "source": r[2],
            "url_name": r[3]
        })
    return jsonify({'categories': data})


@app.route('/articles/<int:category_id>', methods=['GET'])
def get_articles(category_id):
    offset = request.args.get('offset')
    print(offset)
    count = utils.count_article_by_category(category_id)
    rows = utils.get_all_by_category(category_id, offset)
    data = []
    for r in rows:
        data.append(json_modal(r))
    return jsonify({'totalRecords': count[0], 'articles': data})


@app.route('/detail/<int:article_id>', methods=['GET'])
def get_one_article(article_id):
    r = utils.get_article_by_id(article_id)
    d = json_modal(r)
    return jsonify({'article': d})


# @app.route('/trending', methods=['GET'])
# def get_trending():
#     sql = 'SELECT * FROM Category'
#     rows = utils.get_all(sql)
#     data = []
#     for r in rows:
#         data.append({
#             "id": r[0],
#             "name": r[1],
#             "source": r[2]
#         })
#     return jsonify({'categories': data})


# @app.route('/user', methods=['POST'])
# def login():
#     content = request.get_json()
#     if 'email' is None or 'username' is None or 'password' is None:
#         return jsonify({'success': False})
#     success = utils.login(content['email'], content['username'], content['password'])
#     return jsonify({'success': success})


def comment_modal(r):
    return {
            "comment_id": r[0],
            "author": r[1],
            "body": r[2],
            "published_Date": r[3],
            "article_id": r[4]
        }


@app.route('/comment/<int:article_id>', methods=['GET'])
def get_comment(article_id):
    rows = utils.get_comment(article_id)
    data = []
    for r in rows:
        data.append(comment_modal(r))
    return jsonify({'comment': data})


@app.route('/comment', methods=['POST'])
def post_comment():
    comment = request.get_json()
    author = comment["author"]
    body = comment["body"]
    published_date = comment["published_Date"]
    article_id = comment["article_id"]
    success = utils.post_comment(author, body, published_date, article_id)
    return jsonify({'success': success})


@app.route('/top-trending', methods=['GET'])
def top_trending():
    offset = request.args.get('offset')
    trending = utils.get_trending(offset)
    data = []
    for r in trending[0]:
        data.append(json_modal(r))
    return jsonify({'top_trending': data, 'WC_image_url': trending[1]})


if __name__ == '__main__':
    app.run()
