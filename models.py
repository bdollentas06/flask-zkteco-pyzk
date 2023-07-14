from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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