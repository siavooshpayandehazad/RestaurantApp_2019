
import sqlite3
import datetime
import sys, os
import socket

from flask import Flask
from flask import request, jsonify
from flask_restful import abort, Api, Resource
from flask import render_template, make_response

DB_connection = sqlite3.connect("restaurant.db",  check_same_thread=False)
DB_cureser  =  DB_connection.cursor()
DB_cureser.execute("""CREATE TABLE if not exists orderTable (
                    orderedItem text,
                    number text,
                    date text,
                    time text)""")

DB_cureser.execute("""CREATE TABLE if not exists kitchenOrders (
                    orderedItem text,
                    number text,
                    date text,
                    time text,
                    state text)""")

foodList = ["veggiefajitas", "meatballs","cinnamonroll",  "coffee"]
kitchenList = ["veggiefajitas", "meatballs"]

app = Flask(__name__, template_folder='template', static_url_path='/static')
api = Api(app)

print("-"*10)
try:
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    print("local host name:", host_name)
    print("local host IP:", host_ip)
    print("-"*10)
except:
    host_ip = "localhost"
def getMonthsEnd(month, year):
    if month < 12:
        return (datetime.datetime.strptime(f"{year}-{month+1}-01", '%Y-%m-%d')-datetime.timedelta(days=1)).date()
    else:
        return (datetime.datetime.strptime(f"{year+1}-01-01", '%Y-%m-%d')-datetime.timedelta(days=1)).date()

class kitchen(Resource):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        DB_cureser.execute("""SELECT * FROM kitchenOrders WHERE date == ? and state = ? """, ( datetime.date.today(), "incomplete", ))
        orderedItems = DB_cureser.fetchall()
        return make_response(render_template('kitchen.html', orderedItems=orderedItems, host_ip=host_ip),200,headers)


class cashReg(Resource):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('cashregister.html', foodList = foodList, host_ip=host_ip),200,headers)

class waitingroom(Resource):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        DB_cureser.execute("""SELECT * FROM kitchenOrders WHERE date == ? and state = ? """, ( datetime.date.today(), "incomplete", ))
        waiting = DB_cureser.fetchall()
        DB_cureser.execute("""SELECT * FROM kitchenOrders WHERE date == ? and state = ? """, ( datetime.date.today(), "complete", ))
        ready = DB_cureser.fetchall()
        return make_response(render_template('waitingroom.html', waiting_list=waiting, ready_list=ready, host_ip=host_ip),200,headers)

class bookkeeping(Resource):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        monthsBeginning = datetime.date.today().replace(day=1)
        monthsEnd = getMonthsEnd(monthsBeginning.month, monthsBeginning.year)
        DB_cureser.execute("""SELECT * FROM orderTable WHERE date >= ? and date <= ? """, (monthsBeginning, monthsEnd, ))
        orderedItems = DB_cureser.fetchall()
        return make_response(render_template('bookkeeping.html', orderedItems=orderedItems, host_ip=host_ip),200,headers)


@app.route('/save_order', methods=['POST'])
def save_order():
    req_data = request.get_json()
    for item in req_data:
        if item not in ["date", "time"]:
            DB_cureser.execute("""INSERT INTO orderTable VALUES(?, ?, ?, ?)""", (item, req_data[item], req_data["date"], req_data["time"]))
            if item in kitchenList:
                DB_cureser.execute("""INSERT INTO kitchenOrders VALUES(?, ?, ?, ?, ?)""", (item, req_data[item], req_data["date"], req_data["time"], "incomplete"))
        DB_connection.commit()
    return "Done", 200

@app.route('/order_ready', methods=['POST'])
def order_ready():
    req_data = request.get_json()
    print(req_data)
    DB_cureser.execute("""DELETE FROM kitchenOrders WHERE orderedItem = ? and number = ? and date =? and time = ? and state = ?""", (req_data["order"], req_data["number"], req_data["date"], req_data["time"], "incomplete"))
    DB_connection.commit()
    DB_cureser.execute("""INSERT INTO kitchenOrders  VALUES(?, ?, ?, ?, ?)""", (req_data["order"], req_data["number"], req_data["date"], req_data["time"], "complete"))
    DB_connection.commit()
    return "Done", 200

@app.route('/order_taken', methods=['POST'])
def order_taken():
    req_data = request.get_json()
    print(req_data)
    DB_cureser.execute("""DELETE FROM kitchenOrders WHERE orderedItem = ? and number = ? and date =? and time = ? and state = ?""", (req_data["order"], req_data["number"], req_data["date"], req_data["time"], "complete"))
    DB_connection.commit()
    return "Done", 200

api.add_resource(cashReg, '/cashregister.html')
api.add_resource(bookkeeping, '/bookkeeping.html')
api.add_resource(kitchen, '/kitchen.html')
api.add_resource(waitingroom, '/waitingroom.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
