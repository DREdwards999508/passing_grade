import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import Form, BooleanField, StringField, validators

app = Flask(__name__)
app.config.from_object(__name__)

class RegistrationForm(Form):
    username     = StringField('Username', [validators.Length(min=4, max=25)])
    email        = StringField('Email Address', [validators.Length(min=6, max=35)])
    accept_rules = BooleanField('I accept the site rules', [validators.InputRequired()])

class ProfileForm(Form):
    birthday   = DateTimeField('Your Birthday', format ='%m/%d/%y')
    signature  = TextAreaField('Forum Signature')
    
class AdminProfileForm(ProfileForm):
    username = StringField('Username', [validators.Length(max = 40)])
    level    = IntegerField('User Level', [validators.NumberRange(min=0, max=10)])
    
def register(request):
    form = RegistrationForm(request.POST)
    if request.method == 'POST' and form.validate():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.save()
        redirect('register)'
    return render_response('register.html', form = form)

def edit_profile(request):
    user = request.current_user
    form = ProfileForm(request.POST, user)
    if request.method == 'POST' and form.validate():
        form.populate_obj(user)
        user.save()
        redirect('edit_profile')
    return render_response('edit_profile.html', form=form)

def change_username(request):
    user = request.current_user
    form = ChangeUsernameForm(request.POST, user, username = 'silly')
    if request.method == 'POST' and form.validate():
        user.username = form.username.data
        user.save()
        return redirect('change_username')
    return render_response('change_username.html', form=form)

class ChangeEmailForm(Form):
    email = StringField('Email', [validators.Length(min=6, message = (u'Little short for an email address?')), validators.Email(message = (u'That\'s not a valid email address.'))])

class LoginForm(Form):
    username = StringField('Username')
    password = PasswordField('Password')
    
form = LoginForm()
    
if __name__ == '__main__':
    app.run()