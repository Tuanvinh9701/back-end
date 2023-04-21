
from flask import request, Flask, send_file
from pymongo import MongoClient
from bson.json_util import dumps
import json
import random
from flask_bcrypt import Bcrypt
from flask_restful import Resource, Api, reqparse
import werkzeug
# Local imports
from user import User
from googletrans import Translator
import logging, os

import cv2
import pytesseract

APP_URL = "172.20.10.2"

client = MongoClient('mongodb://localhost:27017')

db = client['LearnEnglish']

app = Flask(__name__)

# Create Bcrypt
bc = Bcrypt(app)

file_handler = logging.FileHandler('server.log')
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

PROJECT_HOME = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = '{}/uploads/'.format(PROJECT_HOME)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/translate_eng_vn/", methods = ['POST'])
def transalte_eng_vn():
    try:
        data = json.loads(request.data)['vocab']
        reply = Translator().translate(data['content'], dest='vi').text
        return dumps({'reply' : reply})
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/translate_vn_eng/", methods = ['POST'])
def transalte_vn_eng():
    try:
        data = json.loads(request.data)['vocab']
        reply = Translator().translate(data['content'],dest='en').text
        return dumps({'reply' : reply})
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/add_post", methods = ['POST'])
def add_post():
    try:
        data = json.loads(request.data)['dataPost']
        data["post_id"] = random.randint(1, 10000000)
        data["post_like"] = []
        data["post_comment"] = []
        data["post_save"] = []
        data["userName"] = "VINH TRUONG"
        print(data)
        db.Posts.insert_one(data)
        return dumps({'message' : 'SUCCESS'})
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/update_like/<id>", methods = ['PUT'])
def update_like(id):
    try:
        data = json.loads(request.data)['datalike']
        query = {"post_id": int(id)}
        newvalues = {"$push": {"post_like": data}}
        db.Posts.update_one(query, newvalues)
        return dumps({'message' : 'SUCCESS'})
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_post_with_cate/<label>", methods = ['GET'])
def get_post_with_cate(label):
    try:
        posts = db.Posts.find({"labelCate": label})
        # print(posts.name)
        return dumps(posts)
    except Exception as e:
        return dumps({'error' : str(e)})


@app.route("/get_all_post", methods = ['GET'])
def get_all_post():
    try:
        # get all post reverse
        posts = db.Posts.find().sort('_id', -1)
        # print(posts.name)
        return dumps(posts)
    except Exception as e:
        return dumps({'error' : str(e)})

def create_new_folder(local_dir):
    newpath = local_dir
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    return newpath

@app.route('/OCR/<filename>', methods=['GET'])
def OCR(filename):
    saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    img = cv2.imread(saved_path)
    # print(saved_path)
    text = pytesseract.image_to_string(img, lang='eng')
    os.remove(saved_path)
    return dumps({'reply': text})

@app.route('/uploadImage', methods = ['POST'])
def uploadImage():
    try:
        app.logger.info(app.config['UPLOAD_FOLDER'])
        parser = reqparse.RequestParser()
        #parser.add_argument('FNAME', required=True)
        parser.add_argument('image', type=werkzeug.datastructures.FileStorage, location='files')
        args = parser.parse_args()
        imageFile = args['image']
        filename = imageFile.filename
        print(filename)
        create_new_folder(app.config['UPLOAD_FOLDER'])
        saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        app.logger.info("saving {}".format(saved_path))
        imageFile.save(saved_path)
        return dumps({'message' : 'SUCCESS'})
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_image/<name>", methods = ['GET'])
def get_image(name):
    name = "uploads/" + name
    return send_file(name, mimetype='image/gif')

@app.route("/get_book_with_cateId/<id>", methods = ['GET'])
def get_book_with_cateId(id):
    try:
        x = db.Books.find({"book_cate": int(id)})
        return dumps(x)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_all_vocabs_of_user/<id>", methods = ['GET'])
def get_all_vocabs_of_user(id):
    try:
        x = db.Vocab_User.find_one({"user_id": int(id)}, {'_id': 0})
        return dumps(x['vocabs'])
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/user_add_vocab", methods = ['POST'])
def user_add_vocab():
    try:
        data = json.loads(request.data)['vocab_user']
        vi = data['vi']
        es = data['es']
        user_id = data['user_id']
        query = {"user_id": user_id}
        
        exit_user_vocab = db.Vocab_User.find_one(query, {'_id': 0})
        print(exit_user_vocab)
        if exit_user_vocab == None:
            print(exit_user_vocab)
            db.Vocab_User.insert_one({"user_id": user_id, "vocabs": [{"vi": vi, "es": es, "id": 1}]})
        else:
            vocabs = exit_user_vocab['vocabs']
            newvalues = {"$push": {"vocabs": {"vi": vi, "es": es, "id": len(vocabs) + 1}}}
            db.Vocab_User.update_one(query, newvalues)

        return dumps({'message' : 'SUCCESS'})
    except Exception as e:
        return dumps({'error' : str(e)})

# Login
@app.route('/login', methods=['POST'])
def login():
    # Retrieve user from database
    users = db.Users
    data = json.loads(request.data)['user']
    user_data = users.find_one({'username': data['username']}, {'_id': 0})
    if user_data:
        # Check password hash
        if bc.check_password_hash(user_data['password'], data['password']):
            # Go to profile page after login
            return dumps({'message' : 'Sign in Success', "status" : 200, "user_id": user_data['id'], "full_name": user_data['full_name'], "username": user_data['username'], "verified": user_data['verified']})

    # Redirect to login page on error
    return dumps({'message' : 'Sign in Failed', "status" : 400})
    

@app.route("/register", methods = ['POST'])
def register():
    if request.method == 'POST':
        data = json.loads(request.data)['user']
        # Trim input data
        full_name = data['full_name'].strip()
        username = data['username'].strip()
        password = data['password'].strip()
        role = data['role'].strip()

        users = db.Users
        max_id = users.find().sort( "id", -1 ).limit(1)
        # Check if email address already exists
        existing_user = users.find_one(
            {'username': username, 'full_name': full_name}, {'_id': 0})

        if existing_user is None:
        #     Hash password
            hashpass = bc.generate_password_hash(password).decode('utf-8')
        #     Create user object (note password hash not stored in session)
            new_user = User(full_name, username, password, role)
        #     Create dictionary data to save to database
            user_data_to_save = new_user.dict()
            user_data_to_save['password'] = hashpass
            user_data_to_save['id'] = int(max_id[0]['id']) + 1

        #     Insert user record to database
            if users.insert_one(user_data_to_save):
                return dumps({'message' : "Registration Success", "status" : 200, "data" : user_data_to_save["username"]})
            else:
                # Handle database error
                return dumps({'message' : "Registration Failed", "status" : 500})

        # Handle duplicate email
        return dumps({'message' : "Account already exists", "status" : 400})

    # Return template for registration page if GET request
    return dumps({'message' : "Registration Failed", "status" : 500})


@app.route("/get_all_user", methods = ['GET'])
def get_all_user():
    try:
        users = db.Users.find()
        # print(users.name)
        return dumps(users)
    except Exception as e:
        return dumps({'error' : str(e)})


@app.route("/get_user_id/<id>", methods = ['GET'])
def get_user_id(id):
    try:
        users = db.Users.find_one({"id": int(id)}, {'_id': 0})
        del users['password']
        return dumps(users)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/update_user_id", methods = ['POST'])
def update_user_id():
    try:
        data = json.loads(request.data)['user']
        myquery = { "id": int(data["id"]) }
        print(myquery)
        newvalues = { "$set": { "full_name": data["full_name"], "username": data["username"] } }

        status = db.Users.update_one(myquery, newvalues)
        return dumps({'message' : 'SUCCESS'})
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_all_cate_books", methods = ['GET'])
def get_all_cate_books():
    try:
        cate_books = db.Cate_Books.find()
        print(cate_books)
        return dumps(cate_books)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_news", methods = ['GET'])
def get_news():
    try:
        five_books = db.News.find()
        return dumps(five_books)
    except Exception as e:
        return dumps({'error' : str(e)})


@app.route("/get_recently_books", methods = ['GET'])
def get_recently_books():
    try:
        five_books = db.Books.find()
        five_books_results = [ { "id": book["id"], "title": book["title"], "image": book["image_url"] } for book in five_books ]
        return dumps(five_books_results)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_jump_BackIn", methods = ['GET'])
def get_jump_BackIn():
    try:
        five_books = db.Books.find().sort( "create_date", 1 ).limit(5)
        five_books_results = [ { "id": book["id"], "title": book["title"], "image": book["image_url"] } for book in five_books ]
        return dumps(five_books_results)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/get_best_favorite", methods = ['GET'])
def get_best_favorite():
    try:
        five_books = db.Books.find().sort( "rate", -1 ).limit(5)
        five_books_results = [ { "id": book["id"], "title": book["title"], "image": book["image_url"] } for book in five_books ]
        return dumps(five_books_results)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/add_book_with_user", methods = ['POST'])
def add_book_with_user():
    try:
        data = json.loads(request.data)['bookUser']
        book_title = data['book_title']
        user_id = data['user_id']
        newvalues = {"book_title": book_title, "user_id": user_id}
        existing_user = db.Book_User.find_one(newvalues)

        existing_book = db.Books.find_one({"title": book_title})
        print(existing_book)
        if existing_book != None:
            db.Books.update_one({"title": book_title}, {"$inc": {"rate": 1}})

        if existing_user is None:
            status = db.Book_User.insert_one(newvalues)

        return dumps({'message' : 'SUCCESS', "status" : 200})
    except Exception as e:
        return dumps({'error' : str(e)})



# @app.route("/delete_one_contact/<name>", methods = ['DELETE'])
# def delete_one_contact(name):
#     try:
#         x = db.Contacts.find_one({"name": name})
#         status = db.Contacts.delete_one(x)
#         return dumps({'message' : 'SUCCESS'})
#     except Exception as e:
#         return dumps({'error' : str(e)})

@app.route("/")
def home():
    return "home.html"

if(__name__=="__main__"):
    app.run(host=APP_URL, port=5000, debug = True)
