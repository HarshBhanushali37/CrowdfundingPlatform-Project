from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, FloatField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from datetime import datetime, timedelta
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please use a different one or login.')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    bio = TextAreaField('About Me', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Update Profile')

class CampaignForm(FlaskForm):
    title = StringField('Campaign Title', validators=[DataRequired(), Length(min=5, max=120)])
    short_description = StringField('Short Description (Tagline)', validators=[DataRequired(), Length(max=250)])
    description = TextAreaField('Full Description', validators=[DataRequired()])
    goal_amount = FloatField('Goal Amount (₹)', validators=[DataRequired(), NumberRange(min=1000)])
    category = SelectField('Category', choices=[
        ('emergency', 'Emergency Food Relief'),
        ('community', 'Community Food Programs'),
        ('children', 'Children\'s Nutrition'),
        ('elderly', 'Elderly Support'),
        ('international', 'International Aid'),
        ('education', 'Food Education'),
        ('other', 'Other')
    ])
    location = StringField('Location', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Create Campaign')
    
    def validate_end_date(self, end_date):
        if end_date.data < datetime.now().date():
            raise ValidationError('End date must be in the future.')
        
        if end_date.data > (datetime.now() + timedelta(days=365)).date():
            raise ValidationError('End date must be within one year from now.')

class DonationForm(FlaskForm):
    amount = FloatField('Donation Amount (₹)', validators=[DataRequired(), NumberRange(min=100)])
    comment = TextAreaField('Leave a Comment (Optional)', validators=[Optional(), Length(max=300)])
    anonymous = BooleanField('Make this donation anonymous')
    submit = SubmitField('Complete Donation')

class UpdateForm(FlaskForm):
    title = StringField('Update Title', validators=[DataRequired(), Length(max=120)])
    content = TextAreaField('Update Content', validators=[DataRequired()])
    submit = SubmitField('Post Update')
