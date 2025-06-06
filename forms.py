from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, DateTimeField, IntegerField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    creator_type = SelectField('Creator Type', 
                              choices=[('artist', 'Artist'), ('writer', 'Writer'), 
                                     ('filmmaker', 'Filmmaker'), ('musician', 'Musician'),
                                     ('designer', 'Designer'), ('other', 'Other')])

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    creator_type = SelectField('Creator Type', 
                              choices=[('artist', 'Artist'), ('writer', 'Writer'), 
                                     ('filmmaker', 'Filmmaker'), ('musician', 'Musician'),
                                     ('designer', 'Designer'), ('other', 'Other')])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    website = StringField('Website', validators=[Optional(), Length(max=200)])

class CircleForm(FlaskForm):
    name = StringField('Circle Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    category = SelectField('Category', 
                          choices=[('film', 'Film & Video'), ('music', 'Music & Audio'),
                                 ('art', 'Visual Arts'), ('writing', 'Writing & Literature'),
                                 ('design', 'Design'), ('gaming', 'Gaming'),
                                 ('photography', 'Photography'), ('other', 'Other')])
    max_members = IntegerField('Maximum Members', validators=[DataRequired(), NumberRange(min=2, max=50)])
    is_public = BooleanField('Public Circle')

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=2000)])
    category = SelectField('Category', 
                          choices=[('film', 'Film & Video'), ('music', 'Music & Audio'),
                                 ('art', 'Visual Arts'), ('writing', 'Writing & Literature'),
                                 ('design', 'Design'), ('gaming', 'Gaming'),
                                 ('photography', 'Photography'), ('other', 'Other')])
    funding_goal = FloatField('Funding Goal ($)', validators=[Optional(), NumberRange(min=0)])
    funding_deadline = DateTimeField('Funding Deadline', validators=[Optional()])

class MilestoneForm(FlaskForm):
    title = StringField('Milestone Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    target_date = DateTimeField('Target Date', validators=[Optional()])
