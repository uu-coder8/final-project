from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, FileField, SubmitField, BooleanField, TextAreaField, DateField, IntegerField, SelectField, SelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from flask_wtf.file import FileAllowed
from flask_login import current_user
from models import User,Job
from datetime import date,timedelta



class RegistrationForm(FlaskForm):
    firstname = StringField(label='Firstname', validators=[DataRequired(), Length(max=30)])
    lastname = StringField(label='Lastname', validators=[DataRequired(), Length(max=30)])
    username = StringField(label='Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = EmailField(label='Email Address', validators=[DataRequired(), Email(), Length(max=50)])
    password = PasswordField(label='Pasword', validators=[DataRequired(), Length(min=8, max=60)])
    password_confirm = PasswordField(label='Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    image = FileField(label='Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', '.svg'], 'Images only!')])
    submit = SubmitField(label='Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already registered')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered')


class LoginForm(FlaskForm):
    email = EmailField(label='Email Address', validators=[DataRequired(), Email()])
    password = PasswordField(label='Pasword', validators=[DataRequired()])
    remember = BooleanField(label='Remember me')
    submit = SubmitField(label='Log in')


class AddJobForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(), Length(min=5, max=100)])
    date_posted = DateField(label='Post Date', format="%Y-%m-%d", default=date.today, validators=[DataRequired()])
    date_expire = DateField(label='Expire Date', format="%Y-%m-%d",default=lambda: date.today() + timedelta(days=30), validators=[DataRequired()])
    short_description = TextAreaField('Short Description', validators=[DataRequired(), Length(min=20, max=500)])
    full_description = TextAreaField('Full Description', validators=[DataRequired(), Length(min=50)])
    company = StringField(label='Company', validators=[DataRequired(), Length(max=100)])
    salary = IntegerField(label='Salary',validators=[Optional(),NumberRange(min=0, max=10000000)])
    location = StringField(label='Location', validators=[DataRequired(), Length(max=100)])
    category = SelectField(label='Category',choices=[
                                                    ('IT', 'IT'), 
                                                    ('Law', 'Law'),
                                                    ('Education', 'Education'),
                                                    ('Media', 'Media'), 
                                                    ('Finance','Finance'), 
                                                    ('Marketing','Marketing'),
                                                    ('Design','Design'),
                                                    ('Other','Other')
                                                    ],
                            validators=[DataRequired()] )
    submit = SubmitField(label='Add Job')


    def validate_date_posted(self, date_posted):
        if date_posted.data and date_posted.data < date.today():
            raise ValidationError('Post date cannot be in the past.')
    
    def validate_date_expire(self, date_expire):
        if date_expire.data:
            if date_expire.data < date.today():
                raise ValidationError('Expire date cannot be in the past.')
            if self.date_posted.data and date_expire.data < self.date_posted.data:
                raise ValidationError('Expire date must be after the post date.')



class FilterForm(FlaskForm):
    job_category=SelectMultipleField(label='Category',choices=[
                                                    ('IT', 'IT'), 
                                                    ('Law', 'Law'),
                                                    ('Education', 'Education'),
                                                    ('Media', 'Media'), 
                                                    ('Finance','Finance'), 
                                                    ('Marketing','Marketing'),
                                                    ('Design','Design'),
                                                    ('Other','Other')
                                                    ],
                                                    widget=ListWidget(prefix_label=False),
                                                    option_widget=CheckboxInput())

    salary_range=SelectMultipleField(label='Category',choices=[
                                                    ('1', '$0 - $5,000'), 
                                                    ('2', '$5,000 - $10,000'),
                                                    ('3', '$10,000 - $15,000'),
                                                    ('4', '$15,000+'), 
                                                    ],
                                                    widget=ListWidget(prefix_label=False),
                                                    option_widget=CheckboxInput())

    order_by=SelectField(label='Category',choices=[
                                                    ('1', 'Newest First'), 
                                                    ('2', 'Oldest First'),
                                                    ('3', 'Highest Salary'),
                                                    ('4', 'Lowest Salary'), 
                                                    ])

    submit = SubmitField(label='Apply Filter')

class UpdateJobForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(), Length(min=5, max=100)])
    date_posted = DateField(label='Post Date', format="%Y-%m-%d", validators=[DataRequired()])
    date_expire = DateField(label='Expire Date', format="%Y-%m-%d", validators=[DataRequired()])
    short_description = TextAreaField('Short Description', validators=[DataRequired(), Length(min=20, max=200)])
    full_description = TextAreaField('Full Description', validators=[DataRequired(), Length(min=50)])
    company = StringField(label='Company', validators=[DataRequired(), Length(max=100)])
    salary = IntegerField(label='Salary', validators=[Optional(), NumberRange(min=0, max=10000000)])
    location = StringField(label='Location', validators=[DataRequired(), Length(max=100)])
    category = SelectField(label='Category', choices=[
        ('IT', 'IT'), 
        ('Law', 'Law'),
        ('Education', 'Education'),
        ('Media', 'Media'), 
        ('Finance', 'Finance'), 
        ('Marketing', 'Marketing'),
        ('Design', 'Design'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField(label='Update Job')


class UpdateProfileForm(FlaskForm):
    firstname = StringField(label='Firstname', validators=[DataRequired(), Length(max=30)])
    lastname = StringField(label='Lastname', validators=[DataRequired(), Length(max=30)])
    username = StringField(label='Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = EmailField(label='Email Address', validators=[DataRequired(), Email(), Length(max=50)])
    image = FileField(label='Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'], 'Images only!')])
    submit = SubmitField(label='Save Changes')
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered')

class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField(label='Current Password', validators=[DataRequired()])
    new_password = PasswordField(label='New Password', validators=[DataRequired(), Length(min=8, max=60)])
    confirm_password = PasswordField(label='Confirm New Password', 
                                    validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField(label='Update Password')

class CompareForm(FlaskForm):
    cv = FileField(label='CV file', validators=[DataRequired(),FileAllowed(['docx', 'pdf', 'txt'], 'Only PDF, DOCX, and TXT files are allowed!')])
    submit = SubmitField(label='Compare')
