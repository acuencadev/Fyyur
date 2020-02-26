#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String, nullable=True)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String, nullable=True)
    genres = db.Column(db.String, nullable=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String, nullable=True)
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String, nullable=True)
    website = db.Column(db.String(120), nullable=True)
    
class Show(db.Model):
  __tablename__ = 'Show'
  
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime())
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  
  artist = db.relationship('Artist', backref=db.backref('shows', cascade='all,delete'))
  venue = db.relationship('Venue', backref=db.backref('shows', cascade='all,delete'))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  q = db.session.query(Venue.city, Venue.state).\
                group_by(Venue.city, Venue.state)

  venues = []
  
  for row in q.all():
    venue = {
      'city': row.city,
      'state': row.state,
      'venues': Venue.query.filter_by(city=row.city, state=row.state).all()
    }
    venues.append(venue)
  
  return render_template('pages/venues.html', areas=venues);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  matches = db.session.query(Venue).filter(Venue.name.like(f"%{search_term}%")).all()
  
  response={
    "count": len(matches),
    "data": matches
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  
  if not venue:
    abort(404)
    
  upcoming_shows = db.session.query(Show).join(Show.artist).\
    filter(Show.venue_id == venue_id).\
    filter(Show.start_time >= datetime.utcnow()).all()
    
  past_shows = db.session.query(Show).join(Show.artist).\
    filter(Show.venue_id == venue_id).\
    filter(Show.start_time < datetime.utcnow()).all()
    
  venue.genres = venue.genres.strip('{}').split(',')
  
  data = {
    'venue': venue,
    'upcoming_shows': upcoming_shows,
    'past_shows': past_shows
  }
  
  return render_template('pages/show_venue.html', **data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  venue = Venue(name=form.name.data, city=form.city.data, state=str(form.state.data),
                address=form.address.data, phone=form.phone.data,
                genres=Genre.list_to_string(form.genres.data),
                image_link=form.image_link.data, facebook_link=form.facebook_link.data)
  
  if form.validate_on_submit():
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  venue = Venue.query.get(venue_id)

  if not venue:
    abort(404)
    
  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()

  return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  matches = db.session.query(Artist).filter(Artist.name.like(f"%{search_term}%")).all()
  
  response={
    "count": len(matches),
    "data": matches
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  
  if not artist:
    abort(404)
    
  artist.genres = artist.genres.strip('{}').split(',')
    
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  
  if not artist:
    abort(404)
  
  form = ArtistForm(name=artist.name, city=artist.city, state=artist.state,
                    phone=artist.phone, genres=artist.genres.strip('{}').split(','),
                    image_link=artist.image_link, facebook_link=artist.facebook_link)
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  
  if not artist:
    abort(404)
    
  form = ArtistForm()
  
  if form.validate_on_submit():
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = str(form.state.data)
    artist.phone = form.phone.data
    artist.genres = Genre.list_to_string(form.genres.data)
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
      
    db.session.commit()
    
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    return redirect(url_for('edit_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  
  if not venue:
    abort(404)
  
  form = VenueForm(name=venue.name, city=venue.city, state=venue.state,
                   address=venue.address, phone=venue.phone,
                   genres=venue.genres.strip('{}').split(','),
                   facebook_link=venue.facebook_link)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  
  if not venue:
    abort(404)
  
  form = VenueForm()
  
  if form.validate_on_submit():
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = str(form.state.data)
    venue.genres= Genre.list_to_string(form.genres.data)
    venue.phone = form.phone.data
    venue.address = form.address.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    
    db.session.commit()
  
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    print(form.errors)
    return redirect(url_for('edit_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
    
  artist = Artist(name=form.name.data, city=form.city.data, state=str(form.state.data),
                  phone=form.phone.data, genres=Genre.list_to_string(form.genres.data),
                  image_link=form.image_link.data, facebook_link=form.facebook_link.data)
  
  if form.validate_on_submit():
    db.session.add(artist)
    db.session.commit()
    
    flash('Artist ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  
  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
    
  if form.validate_on_submit():
    artist = Artist.query.get(form.artist_id.data)
    venue = Venue.query.get(form.venue_id.data)
    
    if not artist or not venue:
      flash('An error occurred. Show could not be listed.')
    else:
      show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data,
                  start_time=form.start_time.data)
      
      db.session.add(show)
      db.session.commit()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
