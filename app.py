import os
import json
import requests

from flask import *
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)

with open("api_keys.json") as api_keys_file:
    api_keys = json.loads(api_keys_file)

app.config['MONGO_URI'] = "mongodb://localhost:27017/hackathon2020"
app.secret_key = api_keys["APP_SECRET_KEY"]
mongo = PyMongo(app)
ALLOWED_EXTENSIONS = ['png', 'apng', 'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp', 'gif', 'svg', 'bmp', 'ico', 'cur']

def is_human(captcha_response):
    """
    Validating recaptcha response from google server.
    Returns True if the captcha test passed for submitted form, otherwise it returns False.
    """
    secret = api_keys["CAPTCHA_KEY"]
    payload = {"response": captcha_response, 'secret': secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    return response_text["success"]


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        return render_template('add.html')
    elif request.method == 'POST':
        if is_human(request.form['g-recaptcha-response']):
            files = request.files.getlist("images")
            print(files)
            files_uploaded_to_insert = []
            for file in files:
                name = file.filename
                extension = name.split('.')[-1]
                with open(os.path.join(os.path.dirname(__file__), 'filename.txt'), 'r') as n1:
                    n = f'image{n1.readline().strip()}.{extension}'
                    n1.seek(0)
                    b = n1.readline().strip()
                if extension in ALLOWED_EXTENSIONS:
                    pth = str((os.path.dirname(__file__)).replace('\\', '/'))
                    file.save(os.path.join(pth, 'static/images', n))
                    files_uploaded_to_insert.append(n)
                    with open(os.path.join(pth, 'filename.txt'), 'w') as n2:
                        n2.write(str(int(b)+1))
                else:
                    flash('You Have Uploaded a File Type That We Do Not Support')
                    return redirect('/add')
            mongo.db.products.insert_one(
                {
                    'name': request.form['name'],
                    'address': request.form['address'],
                    'title': request.form['title'],
                    'description': request.form['description'],
                    'length': request.form['length'],
                    'height': request.form['height'],
                    'width': request.form['width'],
                    'files_uploaded': files_uploaded_to_insert
                }
            )
            flash('Donation Succesful! Thank you!')
            return redirect('/')
        else:
            flash('Please Check the Recaptcha Box')
            return redirect('/add')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        items = list(mongo.db.products.find({}))
        return render_template('buy.html', products=items)
    elif request.method == 'POST':
        return redirect('/item/%s' %request.form['item_id'])


@app.route('/item', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        return render_template('item.html', item=mongo.db.products.find_one({'_id': request.form['_id']}))
    elif request.method == 'POST':
        return redirect(f'/buy/{request.form.get("item")}')

@app.route('/buy/<item>', methods=['GET', 'POST'])
def buy(item):
    if request.method == 'GET':
        return render_template('buyformcheckout.html', CLIENT_CAPTCHA_KEY=api_keys["CLIENT_CAPTCHA_KEY"])
    elif request.method == 'POST':
        if is_human(request.form['g-recaptcha-response']):
            for each in mongo.db.products.find_one({'_id': ObjectId(item)})['files_uploaded']:
                pth = str((os.path.dirname(__file__)).replace('\\', '/'))
                os.remove(os.path.join(pth, 'static/images', each))
            mongo.db.products.delete_one({'_id': ObjectId(item)})
            flash('Item Bought')
            return redirect('/')
        else:
            flash('Please Check the Recaptcha Box')
            return redirect('/buy/%s' %item)


@app.route('/image/<filename>')
def image(filename):
    for file in os.listdir(os.path.join(os.path.dirname(__file__), 'static/images')):
        if file == filename:
            return os.path.join('./static/images', filename)

app.add_template_global(image, name='get_image')


if __name__ == '__main__':
    app.run(debug=True)