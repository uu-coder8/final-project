from db import db
from datetime import date, timedelta
from flask_login import UserMixin


class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60),nullable=False)
    image_file = db.Column(db.String(30), nullable=False, default='default.jpg')
    registration_date=db.Column(db.Date, nullable=False, default=date.today)

    jobs = db.relationship('Job', backref='author', lazy=True)

    def __repr__(self):
        return f"User ('{id}', '{username}', '{email}', '{image_file})"


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.Date, nullable=False, default=date.today)
    date_expire = db.Column(db.Date, nullable=False, default=lambda: date.today() + timedelta(days=30))
    short_description = db.Column(db.Text, nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Integer, nullable=True, default=1000)
    location = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Job('{self.title}', '{self.date_posted}','{self.date_expire}', '{self.author.username}', '{self.full_description}', '{self.company}', '{self.salary}', '{self.location}', '{self.category}')"
    