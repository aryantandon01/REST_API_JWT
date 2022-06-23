import pymysql
# from app import app
# from config import mysql
from flask import Flask, request, jsonify, make_response, session, render_template
import jwt
from functools import wraps
import datetime
from app import app
from flaskext.mysql import MySQL
from flask import Flask
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'JustDemonstrating'
CORS(app)

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '@driBOY01'
app.config['MYSQL_DATABASE_DB'] = 'db_ecom_stock'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


def check_for_token(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Message': 'Missing Token'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except Exception as e:
            return jsonify({'Message': str(e)}), 403
        return func(*args, **kwargs)
    return wrapped


@app.route('/')
def index():
    if not session.get('logged in'):
        return render_template('login.html')
    else:
        return 'Currently Logged In'


@app.route('/public')
def public():
    return 'Anyone can view this'


@app.route('/auth')
@check_for_token
def authorised():
    return 'This is a secret'


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] and request.form['password'] == 'password':
        session['logged in'] = True
        token = jwt.encode({
            'user': request.form['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        },
        app.config['SECRET_KEY'])
        return jsonify({'token': token})
    else:
        return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic Realm: "Login Required"'})


@app.route('/product', methods=['POST'])
@check_for_token
def create_emp():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        _json = request.json
        _category_name = _json['category_name']
        _mrp = _json['mrp']
        _price = _json['price']
        if _category_name and _mrp and _price and request.method == 'POST':
            sqlQuery = "INSERT INTO prod(category_name, mrp, price) VALUES(%s, %s, %s)"
            bindData = (_category_name, _mrp, _price)
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            response = jsonify('Product added successfully!')
            response.status_code = 200
            return response
        else:
            return showMessage()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/product', methods=['GET'])
# @check_for_token
def emp():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT category_id, category_name, mrp, price, concat((mrp - price)/mrp * 100) AS disc_percentage FROM prod")
        empRows = cursor.fetchall()
        response = jsonify(empRows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/product/<category_id>', methods=['GET'])
# @check_for_token
def emp_details(category_id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT category_id, category_name, mrp, price, concat((mrp - price)/mrp * 100) AS disc_percentage FROM prod WHERE category_id =%s", category_id)
        empRow = cursor.fetchone()
        response = jsonify(empRow)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/product', methods=['PUT'])
# @check_for_token
def update_emp():
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        _json = request.json
        _category_id = _json['category_id']
        _category_name = _json['category_name']
        _mrp = _json['mrp']
        _price = _json['price']
        if _category_name and _mrp and _price and _category_id and request.method == 'PUT':
            sqlQuery = "UPDATE prod SET category_name=%s, mrp=%s, price=%s WHERE category_id=%s"
            bindData = (_category_name, _mrp, _price, _category_id,)
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            response = jsonify('Product updated successfully!')
            response.status_code = 200
            return response
        else:
            return showMessage()
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route("/product/<category_id>", methods=['DELETE'])
# @check_for_token
def delete_emp(category_id):
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM prod WHERE category_id =%s", (category_id,))
        conn.commit()
        response = jsonify('Product deleted successfully!')
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.errorhandler(404)
def showMessage(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
    }
    response = jsonify(message)
    response.status_code = 404
    return response


if __name__ == '__main__':
    app.run(debug=True)
