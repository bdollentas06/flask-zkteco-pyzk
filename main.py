import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, make_response, session
from zk import ZK, const
from flask_sqlalchemy import SQLAlchemy

# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
load_dotenv()
# Database
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = '{}://{}:{}@{}:{}/{}'.format(os.getenv("DB_CONNECTION"), os.getenv("DB_USERNAME"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT"), os.getenv("DB_DATABASE"))
# Binds other database
app.config['SQLALCHEMY_BINDS'] = { 'nkti_adg': '{}://{}:{}@{}:{}/{}'.format(os.getenv("DB_CONNECTION"), os.getenv("ADG_DB_USERNAME"), os.getenv("ADG_DB_PASSWORD"), os.getenv("ADG_DB_HOST"), os.getenv("ADG_DB_PORT"), os.getenv("ADG_DB_DATABASE"))}
app.config['SECRET_KEY'] = os.getenv("JWT_SECRET")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db.init_app(app)

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            token = token.split(' ')
            token = token[1]
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({
                'message' : 'Token is invalid!'
            }), 401
        # returns the current logged in users context to the routes
        return  f(*args, **kwargs)
  
    return decorated
    
class BiometricDevices(db.Model):
    __bind_key__ = 'nkti_adg'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(129))
    port = db.Column(db.String(20))
    status = db.Column(db.Integer)
    deleted_at = db.Column(db.DateTime, nullable=True)
    def __init__(self, host, port, status):
        self.host = host
        self.port = port
        self.status = status
    class Meta:
        db_table = "biometric_devices"

class BiometricRfidUsers(db.Model):
    __bind_key__ = 'nkti_adg'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    device_user_id = db.Column(db.Integer)
    unique_id = db.Column(db.String(9))
    def __init__(self, user_id, device_user_id, unique_id):
        self.user_id = user_id
        self.device_user_id = device_user_id
        self.unique_id = unique_id
    class Meta:
        db_table = "biometric_rfid_users"

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(191))
    email = db.Column(db.String(191))
    password = db.Column(db.String(191))
    status = db.Column(db.Integer())
    remember_token = db.Column(db.String(191))
    
@app.route('/sync-all-finger', methods=["POST"])
@token_required
def sync_all(): 
    conn = None
    devices = BiometricDevices.query.filter(BiometricDevices.status == 1, BiometricDevices.deleted_at == None)
    for device in devices:
    # create ZK instance
        zk = zkInit(device.host, device.port)
        other_device = BiometricDevices.query.filter(BiometricDevices.id != device.id, BiometricDevices.status == 1, BiometricDevices.deleted_at == None)
        try:
            # connect to device
            conn = zk.connect()
            # disable device, this method ensures no activity on the device while the process is run
            conn.disable_device()
            # another commands will be here!
            #Example: Get All Users
            users = conn.get_users()
            for index, user in enumerate(users):
                index_finger = []
                for i in range(10):
                    fingerprint = conn.get_user_template(uid=user.uid, temp_id=i)
                    if fingerprint:
                       index_finger.append(fingerprint)
                for zkdevice in other_device:
                    try:
                        teco = zkInit(zkdevice.host, zkdevice.port)
                        connect = teco.connect()
                        connect.disable_device()
                        connect.save_user_template(user, index_finger)
                        connect.enable_device()
                    except Exception as e:
                        continue

                print (index+1,'out of',len(users),'users fingerprints synced')
                print ('+ UID        : {}'.format(user.uid))
                print ('  Name       : {}'.format(user.name))
                print ('  User  ID   : {}'.format(user.user_id))

            conn.test_voice()
            # re-enable device after all commands already executed
            conn.enable_device()
        except Exception as e:
            print ("Process terminate : {}".format(e))
        finally:
            if conn:
                conn.disconnect()
    return jsonify({'msg': "hello world"})

@app.route('/per-user-sync-finger', methods=["POST"])
@token_required
def sync_per_user():
    user_id = request.json['id']
    conn = None
    devices = BiometricDevices.query.filter(BiometricDevices.status == 1, BiometricDevices.deleted_at == None)
    for device in devices:
        zk = zkInit(device.host, int(device.port))
        other_device = BiometricDevices.query.filter(BiometricDevices.id != device.id, BiometricDevices.status == 1, BiometricDevices.deleted_at == None)
        print()
        try:
            # connect to device
            conn = zk.connect()
            # disable device, this method ensures no activity on the device while the process is run
            conn.disable_device()
            # another commands will be here!
            bio = BiometricRfidUsers.query.filter_by(user_id = user_id).first() ## user_id should be request id todo
            users = conn.get_users()
            find_user = None
            for user in users:
                if user.uid == bio.device_user_id:
                   find_user = user
                   break 
            index_finger = []
            for i in range(10): 
                fingerprint = conn.get_user_template(uid=bio.device_user_id, temp_id=i)
                if fingerprint:
                    index_finger.append(fingerprint)
            for zkdevice in other_device:
                try:
                    teco = zkInit(zkdevice.host, int(zkdevice.port))
                    connect = teco.connect()
                    connect.disable_device()
                    connect.save_user_template(find_user, index_finger)
                    connect.enable_device()
                except Exception as e:
                    continue
            conn.test_voice()
            # re-enable device after all commands already executed
            conn.enable_device()
        except Exception as e:
            print ("Process terminate : {}".format(e))
        finally:
            if conn:
                conn.disconnect()
    return jsonify({"msg": "User successfully synced"})

def zkInit(host, port):
    return ZK(host, port=int(port), timeout=5, password=0, force_udp=False, ommit_ping=False)

if __name__ == "__main__":
    app.run(debug=True)



