import random

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('mongodb://datingSite:datingSite@localhost',27017)
client = MongoClient('localhost', 27017)
db = client.date_siting

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'apple'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib

#################################
##  HTML을 주는 부분             ##
#################################
@app.route('/')
def home():
   return render_template('index.html')

@app.route('/login')
def login():
   return render_template('login_try1.html')

@app.route('/register')
def register():
   return render_template('register_try1.html')

@app.route('/myPage')
def myPage():
   return render_template('my_page.html')

@app.route('/messenger')
def messenger():
   return render_template('messenger.html')

@app.route('/sending_message')
def sending_message():
    recv = request.args.get('recv')
    return render_template('sending_message.html', recv=recv)

@app.route('/messenger_receive')
def messenger_receive():
   return render_template('messenger_receive.html')

@app.route('/messenger_send')
def messenger_send():
   return render_template('messenger_send.html')

@app.route('/matching')
def matching():
   return render_template('matching.html')

@app.route('/introduction')
def introduction():
   return render_template('introduction.html')



#################################
##  로그인을 위한 API            ##
#################################

# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/register', methods=['POST'])
def api_register():
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']
   nickname_receive = request.form['nickname_give']
   sex_receive = request.form['sex_give']
   age_receive = request.form['age_give']

   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

   db.user.insert_one({'id':id_receive,'pw':pw_hash, 'nickname':nickname_receive, 'sex':sex_receive, 'age':age_receive})

   return jsonify({'result': 'success'})


# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']

   # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

   # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
   result = db.user.find_one({'id':id_receive,'pw':pw_hash})

   # 찾으면 JWT 토큰을 만들어 발급합니다.
   if result is not None:
      # JWT 토큰에는, payload와 시크릿키가 필요합니다.
      # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
      # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
      # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
      payload = {
         'id': id_receive,
         'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
      }
      token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

      # token을 줍니다.
      return jsonify({'result': 'success','token':token})
   # 찾지 못하면
   else:
      return jsonify({'result': 'fail', 'msg':'아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/api/nick', methods=['GET'])
def api_valid():
   token_receive = request.headers['token_give']

   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      print(payload)

      userinfo = db.user.find_one({'id':payload['id']},{'_id':0})
      return jsonify({'result': 'success','nickname':userinfo['nickname']})
   except jwt.ExpiredSignatureError:
      # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
      return jsonify({'result': 'fail', 'msg':'로그인 시간이 만료되었습니다.'})

# 시 저장하기
@app.route('/api/myPage', methods=['POST'])
def api_myPage():
   poemTitle_receive = request.form['poemTitle_give']
   poem_receive = request.form['poem_give']
   poem_one_receive = request.form['poem_one_give']
   token_receive = request.headers['token_give']
   payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
   userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})

   if poem_one_receive == 'Y':
      db.poem.update_many({}, {'$set': {'poemOne': 'N'}})

   db.poem.insert_one({'poemTitle':poemTitle_receive,'poem':poem_receive, 'poemOne':poem_one_receive, 'id':userinfo['id']})

   return jsonify({'result': 'success'})

# 시 불러오기(여러개)
@app.route('/api/myPage', methods=['GET'])
def api_get_myPage():
    token_receive = request.headers['token_give']
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
    poems = list(db.poem.find({'id': payload['id']}, {'_id': 0}))

    return jsonify({'result': 'success', 'poems': poems})

# 시 불러오기(하나)
@app.route('/api/myPoem', methods=['GET'])
def api_get_myPoem():
    token_receive = request.headers['token_give']
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
    poemTitle_receive = request.args.get('poemTitle_give')
    poem = db.poem.find_one({'id': payload['id'], 'poemTitle':poemTitle_receive}, {'_id': 0})

    return jsonify({'result': 'success', 'poem': poem})


# 시 수정/업데이트하기
@app.route('/api/myPoem', methods=['POST'])
def api_update_myPage():
    poemTitle_receive = request.form['poemTitle_give']
    poem_receive = request.form['poem_give']
    poem_one_receive = request.form['poem_one_give']

    if poem_one_receive == 'Y':
        db.poem.update_many({}, {'$set': {'poemOne': 'N'}})

    db.poem.update_one({'poemTitle': poemTitle_receive},
                       {'$set': {'title': poemTitle_receive, 'poem': poem_receive, 'poemOne': poem_one_receive}})

    return jsonify({'result': 'success'})

# 매칭 시 띄우기
@app.route('/api/matching', methods=['GET'])
def api_matching():
    token_receive = request.headers['token_give']
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
    poems = list(db.poem.find({}, {'_id': 0}))
    target_poems = []
    for poem in poems:
        poem_user = db.user.find_one({'id': poem['id']}, {'_id': 0})
        if poem_user['sex'] != userinfo['sex'] and poem_user['age'][0] == userinfo['age'][0]:
            target_poems.append(poem)
    if len(target_poems) > 3:
        target_poems = random.sample(target_poems, 3)
    return jsonify({'result': 'success', 'poems': target_poems})

# 편지 저장하기
@app.route('/api/sending_message', methods=['POST'])
def api_sending_message():
   message_receive = request.form['message_give']
   recv_receive = request.form['recv_give']
   token_receive = request.headers['token_give']
   payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
   userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})


   db.sending_message.insert_one({'message':message_receive, 'id':userinfo['id'], 'recv':recv_receive})

   return jsonify({'result': 'success'})

# 보낸 편지 보여주기
@app.route('/api/messenger_send', methods=['GET'])
def api_messenger_send():
    token_receive = request.headers['token_give']
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
    messages = list(db.sending_message.find({}, {'_id': 0}))
    target_messages = []
    for sending_message in messages:
        message_user = db.user.find_one({'id': sending_message['id']}, {'_id': 0})
        if message_user['id'] == userinfo['id']:
            target_messages.append(sending_message)
    return jsonify({'result': 'success', 'messages': target_messages})


if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)