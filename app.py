from flask import Flask, redirect, url_for, render_template, request, session, flash
from zk import ZK, const
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:3306/nkti_adg'
app.config['SECRET_KEY'] = "random string"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class BiometricDevices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(129))
    port = db.Column(db.String(20))
    status = db.Column(db.Integer)
    def __init__(self, host, port, status):
        self.host = host
        self.port = port
        self.status = status
    class Meta:
        db_table = "biometric_devices"

class BiometricRfidUsers(db.Model):
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

@app.route('/sync-all-finger', methods=["POST", "GET"])
def sync_all(): 
    conn = None
    devices = BiometricDevices.query.filter_by(status = 1)
    for device in devices:
    # create ZK instance
        zk = zkInit(device.host, device.port)
        other_device = BiometricDevices.query.filter(BiometricDevices.id != device.id, BiometricDevices.status == 1)
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
    return "hello world"

def zkInit(host, port):
    return ZK(host, port=int(port), timeout=5, password=0, force_udp=False, ommit_ping=False)

@app.route('/per-user-sync-finger', methods=["POST", "GET"])
def sync_per_user():
    conn = None
    devices = BiometricDevices.query.filter_by(status = 1)
    for device in devices:
        zk = zkInit(device.host, int(device.port))
        other_device = BiometricDevices.query.filter(BiometricDevices.id != device.id, BiometricDevices.status == 1)
        try:
            # connect to device
            conn = zk.connect()
            # disable device, this method ensures no activity on the device while the process is run
            conn.disable_device()
            # another commands will be here!
            bio = BiometricRfidUsers.query.filter_by(user_id = 4).first() ## user_id should be request id todo
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
    return "Synced user fingerprints"

if __name__ == "__main__":
    app.run(debug=True)



