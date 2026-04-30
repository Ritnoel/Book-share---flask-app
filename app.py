from flask_sqlalchemy import SQLAlchemy
import flask
from flask import request, render_template, redirect, url_for, session, flash
import postgresqlite
import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, BooleanField, TelField, DateField
from wtforms.validators import InputRequired, ValidationError, NumberRange, Length
from flask_wtf.file import FileAllowed, FileRequired
import os
from string_generator import random_string
from datetime import date


app = flask.Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = postgresqlite.get_uri()
app.config['SECRET_KEY'] = 'mysecretkey'


db = SQLAlchemy(app)

# Book.borrower_id answers "who has this book right now?"
# Borrow answers "who has ever borrowed this book and when


# DATABASE TABLES
class Borrow(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    book_id = sa.Column(sa.Integer, sa.ForeignKey('book.id'))
    date_requested = sa.Column(sa.Date)
    status = sa.Column(sa.String, default="pending")
    borrow_user = db.relationship('User', foreign_keys='Borrow.user_id', back_populates='user_borrow_history')
    borrow_book = db.relationship('Book', foreign_keys='Borrow.book_id', back_populates='book_borrow_history')


class User(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String)
    login_link = sa.Column(sa.String)
    phone_number = sa.Column(sa.String)
    privacy_statement = sa.Column(sa.Boolean, default=False)
    owned_books = db.relationship('Book', foreign_keys='Book.owner_id', back_populates='owner')
    borrowed_books = db.relationship('Book', foreign_keys='Book.borrower_id', back_populates='borrower')
    user_borrow_history = db.relationship('Borrow', foreign_keys='Borrow.user_id', back_populates='borrow_user')


class Book(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    date_added = sa.Column(sa.Date)
    title = sa.Column(sa.String)
    description = sa.Column(sa.String)
    book_photo = sa.Column(sa.String)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    owner = db.relationship('User', foreign_keys='Book.owner_id', back_populates='owned_books')
    borrower_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    borrower = db.relationship('User', foreign_keys='Book.borrower_id', back_populates='borrowed_books')
    book_borrow_history = db.relationship('Borrow', foreign_keys='Borrow.book_id', back_populates='borrow_book', cascade='all, delete-orphan')


# FORMS
class CreateAccountForm(FlaskForm):
    username = StringField('UserName', render_kw={"placeholder": "UserName"}, validators=[InputRequired(message="Please enter your name")])
    phone_number = TelField('Phone Number', render_kw={"placeholder": "Phone Number"}, validators=[InputRequired(message="Please enter your phone number")])
    privacy_statement = BooleanField("I've read the privacy statement and i accept", validators=[InputRequired(message="Please agree to the terms of service")])


class LoginForm(FlaskForm):
    phone_number = TelField('Phone Number', render_kw={"placeholder": "Phone Number"}, validators=[InputRequired()])


class AddbookForm(FlaskForm):
    title = StringField('Title', render_kw={"placeholder": "Title"}, validators=[InputRequired()])
    description = StringField('Description', render_kw={"placeholder": "Description"}, validators=[InputRequired()])
    book_photo = FileField('Book Photo', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!'), FileRequired('You must upload a picture')])


class DateForm(FlaskForm):
    date_requested = DateField('Date', validators=[InputRequired()])


class EmptyForm(FlaskForm):
    pass


# HELPER FUNCTIONS
def check_if_user_in_session():
    if 'user_id' not in session:
        return redirect(url_for('show_login_form'))
    return None


# ROUTES
@app.route('/create_account', methods=['GET'])
def show_create_account_form():
    form = CreateAccountForm()

    return render_template('create_account.html', form=form)


@app.route('/create_account/submit', methods=['POST'])
def submit_create_account_form():
    form = CreateAccountForm()

    if not form.validate_on_submit():
        return render_template('create_account.html', form=form)
    
    # name = form.name.data
    # phone_number = form.phone_number.data

    new_user = User()
    form.populate_obj(new_user)
    db.session.add(new_user)
    db.session.commit()

    user_id = new_user.id
    session['user_id'] = user_id
    
    return redirect(url_for('main'))


@app.route('/login', methods=['GET'])
def show_login_form():
    form = LoginForm()

    return render_template('login.html', form=form)


@app.route('/login/submit', methods=['POST'])
def submit_login_form():
    form = LoginForm()

    if not form.validate_on_submit():
        return render_template('login.html', form=form)
    
    phone_number = form.phone_number.data
    existing_user = User.query.filter_by(phone_number=phone_number).first()

    if not existing_user:
        flash("Phone_number not found", "error")
        # return redirect(url_for('login'))
        return render_template('login.html', form=form)
    
    user_id = existing_user.id
    session['user_id'] = user_id

    return redirect(url_for('main'))


@app.route('/', methods=['GET'])
def main():

    check = check_if_user_in_session()
    if check:
        return check

    form = LoginForm()

    books = Book.query.order_by(Book.date_added.desc()).all()

    return render_template('main.html', form=form, books=books)


@app.route('/add_book', methods=['GET'])
def show_add_book_form():

    check = check_if_user_in_session()
    if check:
        return check

    form = AddbookForm()

    return render_template('addbook.html', form=form)


@app.route('/add_book/submit', methods=['POST'])
def submit_add_book_form():

    check = check_if_user_in_session()
    if check:
        return check
    
    form = AddbookForm()

    if form.validate_on_submit():
    
        if form.book_photo.data:
            r_string = random_string()
            file_name = r_string
            save_to_path = os.path.join("static", "images", file_name)
            form.book_photo.data.save(save_to_path)

        new_book = Book()
        form.populate_obj(new_book)
        new_book.book_photo = file_name
        new_book.date_added = date.today()
        new_book.owner_id = session.get('user_id')

        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for('main'))
    
    return render_template('addbook.html', form=form)


@app.route("/request_book/<int:book_id>", methods=['GET'])
def show_request_book(book_id):

    check = check_if_user_in_session()
    if check:
        return check

    book = Book.query.get_or_404(book_id)

    form = DateForm()
   
    return render_template('request.html', form=form, book=book)


@app.route("/request_book/submit/<int:book_id>", methods=['POST'])
def submit_request_book(book_id):

    check = check_if_user_in_session()
    if check:
        return check
    
    book = Book.query.get_or_404(book_id)

    form = DateForm()
    
    if not form.validate_on_submit():
        return render_template('request.html', form=form, book=book)
    
    new_request = Borrow()
    form.populate_obj(new_request)
    new_request.book_id = book_id
    new_request.user_id = session.get('user_id')

    db.session.add(new_request)
    db.session.commit()

    return redirect(url_for('main'))


@app.route("/user_profile", methods=['POST', 'GET'])
def user_profile():
    """show the current users books not all books and you get it from the session
    """

    check = check_if_user_in_session()
    if check:
        return check

    form = EmptyForm()

    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    my_books = user.owned_books

    incoming_requests = Borrow.query.join(Book).filter(Book.owner_id == user_id).all()

    my_requests = Borrow.query.filter(Borrow.user_id == user_id).all()
   
    return render_template('userprofile.html', form=form, my_books=my_books, incoming_requests=incoming_requests, my_requests=my_requests)


@app.route("/accept/<int:borrow_id>", methods=['GET', 'POST'])
def accept(borrow_id):

    accept_status = Borrow.query.get_or_404(borrow_id)
    accept_status.status = "accepted"

    db.session.commit()
    
    return redirect(url_for('user_profile'))


@app.route("/reject/<int:borrow_id>", methods=['GET', 'POST'])
def reject(borrow_id):

    reject_status = Borrow.query.get_or_404(borrow_id)
    reject_status.status = "rejected"

    db.session.commit()
   
    return redirect(url_for('user_profile'))


@app.route('/delete/<int:book_id>', methods=['POST'])
def delete(book_id):

    delete_book = Book.query.get_or_404(book_id)

    db.session.delete(delete_book)
    db.session.commit()

    return redirect(url_for('user_profile'))


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):

    book = Book.query.get_or_404(book_id)
    form = AddbookForm(obj=book)

    if form.validate_on_submit():
    
        old_image = book.book_photo
        book.title = form.title.data
        book.description = form.description.data

        if form.book_photo.data:
            if old_image:
                old_path = os.path.join("static", "images", old_image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            r_string = random_string()
            file_name = r_string
            save_to_path = os.path.join("static", "images", file_name)
            form.book_photo.data.save(save_to_path)
            book.book_photo = r_string
        else:
            book.book_photo = old_image

        db.session.commit()
        return redirect(url_for('main'))

    return render_template('editbook.html', form=form, book=book)


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('show_login_form'))


with app.app_context():
    # db.drop_all()
    db.create_all()
