from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import os
import requests

API_KEY = os.environ["API_KEY"]
API_ENDPOINT = "https://api.themoviedb.org/3"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(250), unique=False, nullable=False)
    rating = db.Column(db.Float, unique=False, nullable=False)
    ranking = db.Column(db.Integer, unique=False, nullable=False)
    review = db.Column(db.String(250), unique=False, nullable=False)
    img_url = db.Column(db.String(250), unique=False, nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


db.create_all()


class Form(FlaskForm):
    rating = FloatField('Your Rating (0-10)', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

# class RatingForm(FlaskForm):
#     title = StringField('Movie Title', validators=[DataRequired()])
#     submit = SubmitField('Add Movie')


@app.route("/")
def home():

    my_session = db.session.query(Movie)
    all_movies = my_session.order_by(desc(Movie.rating)).all()
    db_size = len(all_movies)
    n = db_size
    for movie in all_movies:
        movie.ranking = n
        n -= 1
        db.session.commit()
    # all_movies = db.session.query(Movie).all()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = Form()
    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        id_movie = request.args.get('id')
        movie = Movie.query.filter_by(id=id_movie).first()
        movie.rating = rating
        movie.review = review
        db.session.commit()

        return redirect('/')

    return render_template('edit.html', form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id', type=int)
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect('/')


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddForm()
    # form_rating = RatingForm()
    if form.validate_on_submit():
        title = form.title.data
        params = {
            'api_key': API_KEY,
            'query': title,
        }
        r = requests.get(url=f"{API_ENDPOINT}/search/movie", params=params)
        r.raise_for_status()
        movie_list = r.json()['results']

        return render_template('select.html', form=form, movie_list=movie_list)

    return render_template('add.html', form=form)


@app.route("/select", methods=['GET', 'POST'])
def select():
    if request.method == 'GET':
        movie_id = request.args.get('id', type=int)
        params = {
            'api_key': API_KEY,
        }
        r = requests.get(url=f"{API_ENDPOINT}/movie/{movie_id}", params=params)
        r.raise_for_status()
        movie_details = r.json()

        new_movie = Movie(
            title=movie_details['original_title'],
            year=movie_details['release_date'],
            description=movie_details['overview'],
            rating=0,
            ranking=2,
            review='',
            img_url=f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for('edit', id=new_movie.id))

    # return render_template('select.html')


if __name__ == '__main__':
    app.run(debug=True)
