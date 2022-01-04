#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    jsonify
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Venue, Artist, Show



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)

#----------------------------------------------------------------------------#
# Database
#----------------------------------------------------------------------------#
db.init_app(app)
migrate = Migrate(app, db)

# TODO:Done Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
# Changed tables so that they are all small letters
# Moved the models to models.py
# flask db migrate
# flask db upgrade
# 
#----------------------------------------------------------------------------#
# Functions
#----------------------------------------------------------------------------#

def past_shows(shows):
  past_shows_info = []

  for show in shows:
    if show.start_time <= datetime.now():
      show_artist = Artist.query.filter_by(id=show.artist_id).first()
      past_shows_info.append({
        "aritist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "venue_id":show.venue_id,
        "venue_name":show.venue.name,
        "venue_image_link":show.venue.image_link,
        "start_time":show.start_time.strftime("%Y-%m-%d %H:%M:%S") 
      })
      
  return past_shows_info

def upcoming_shows(shows):
  upcoming_shows_info = []

  for show in shows:
    if show.start_time > datetime.now():
      show_artist = Artist.query.filter_by(id=show.artist_id).first()
      upcoming_shows_info.append({
        "aritist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "venue_id":show.venue_id,
        "venue_name":show.venue.name,
        "venue_image_link":show.venue.image_link,        
        "start_time":show.start_time.strftime("%Y-%m-%d %H:%M:%S") 
      })
      
  return upcoming_shows_info

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime
 
def flash_errors(form):
  """Flashes form errors"""
  for field, errors in form.errors.items():
    for error in errors:
      flash(u"Error in the %s field - %s" % (
        getattr(form, field).label.text,error), 'error')

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
  # TODO:Done replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # Create a variable to store all of the information for venues
  data = []
  # Get the current time
  current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')
  # Gather all of the areas so we can loop through them  
  all_areas = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  # Loop through each city state combination and process
  for area in all_areas:
    # Get all of the venues in this city state combination
    area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    # Define a variable to store the venue data and loop and store
    venue_data = []
    for venue in area_venues:
      upcoming_shows = Show.query.filter_by(venue_id=venue.id).all()
      venue_data.append({
        "id": venue.id,
        "name": venue.name, 
        "num_upcoming_shows": len(upcoming_shows)
      })
    data.append({
      "city": area.city,
      "state": area.state, 
      "venues": venue_data
    })
  # return the result
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  print('in search')
  # TODO:Done implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()
  # Create response to store the result of the search
  response = {
      "count": len(venues),
      "data": []
  }
  # Add each of the found venues to response
  for venue in venues:
      response["data"].append({
          'id': venue.id,
          'name': venue.name,
      })
  # Return the result of the search
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO:Done replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter_by(id=venue_id).first()
  shows = Show.query.filter_by(venue_id=venue_id).all()
  venue_past_shows = past_shows(shows)
  venue_upcoming_shows = upcoming_shows(shows)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": venue_past_shows,
    "upcoming_shows": venue_upcoming_shows,
    "past_shows_count": len(venue_past_shows),
    "upcoming_shows_count": len(venue_upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO:Done insert form data as a new Venue record in the db, instead
  # TODO:Done modify data to be the data object returned from db insertion
  form = VenueForm(request.form, meta={"csrf": False})

  try:
    # get all of the data
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website = form.website.data
    image_link = form.image_link.data

    seeking_talent = False
    if 'seeking_talent' in request.form:
      seeking_talent = True

    seeking_description = form.seeking_description.data

    if form.validate():
      print("validated")
      # define new venue instance and insert to db
      venue = Venue(name=name, city=city, state=state, address=address,
                  phone=phone, genres=genres, facebook_link=facebook_link,
                  website=website, image_link=image_link,
                  seeking_talent=seeking_talent,
                  seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()

      # TODO:Done on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      print("error")
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')     
      flash_errors(form)

  except:
    # TODO:Done on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()


  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO:Done Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
     venue = Venue.query.get(venue_id)
     venue_name = venue.name
     db.session.delete(venue)
     db.session.commit()
     flash('The Venue ' + venue_id + ' ' + venue_name + ' has been successfully deleted!')
  except:
    db.session.rollback()
    flash('Delete was unsuccessful. Try again!')
  finally:
    db.session.close()


  # BONUS CHALLENGE: Done Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO:Done replace with real data returned from querying the database
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO:Done implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()
  # Create response to store the result of the search
  response = {
      "count": len(artists),
      "data": []
  }
  # Add each of the found venues to response
  for artist in artists:
      response["data"].append({
          'id': artist.id,
          'name': artist.name,
      })
  # Return the result of the search
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))




  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO:Done replace with real artist data from the artist table, using artist_id
  artist = Artist.query.filter_by(id=artist_id).first()
  shows = Show.query.filter_by(artist_id=artist_id).all()
  artist_past_shows = past_shows(shows)
  artist_upcoming_shows = upcoming_shows(shows)

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": artist_past_shows,
    "upcoming_shows": artist_upcoming_shows,
    "past_shows_count": len(artist_past_shows),
    "upcoming_shows_count": len(artist_upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  form = ArtistForm(obj=artist)
  
  # TODO:Done populate form with fields from artist with ID <artist_id>
  edit_artist = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
 }
  return render_template('forms/edit_artist.html', form=form, artist=edit_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form, meta={"csrf": False})  

  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    # get all of the data
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data
    artist.website = form.website.data
    artist.image_link = form.image_link.data

    artist.seeking_venue = False
    if 'seeking_venue' in request.form:
      artist.seeking_venue = True

    artist.seeking_description = form.seeking_description.data

    if form.validate():
      # define venue from entered data and add it to db
      artist = Artist(name=artist.name, city=artist.city, state=artist.state, 
                   phone=artist.phone, genres=artist.genres, facebook_link=artist.facebook_link,
                   website=artist.website, image_link=artist.image_link,
                   seeking_venue=artist.seeking_venue,
                   seeking_description=artist.seeking_description)
      db.session.commit()

      # TODO:Done on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
      flash_errors(form)


  except:
    # TODO:Done on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):


  venue = Venue.query.filter_by(id=venue_id).first()
  form = VenueForm(obj=venue)

  # TODO:Done populate form with values from venue with ID <venue_id>
  venue = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
 }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO:Done take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form, meta={"csrf": False})  

  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    # get all of the data
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.genres = form.genres.data
    venue.facebook_link = form.facebook_link.data
    venue.website = form.website.data
    venue.image_link = form.image_link.data

    venue.seeking_talent = False
    if 'seeking_talent' in request.form:
      venue.seeking_talent = True

    venue.seeking_description = form.seeking_description.data
    if form.validate():
    # define venue from entered data and add it to db
      venue = Venue(name=venue.name, city=venue.city, state=venue.state, address=venue.address,
                    phone=venue.phone, genres=venue.genres, facebook_link=venue.facebook_link,
                    website=venue.website, image_link=venue.image_link,
                    seeking_talent=venue.seeking_talent,
                    seeking_description=venue.seeking_description)
      db.session.commit()

      # TODO:Done on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')

    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')   
      flash_errors(form)

  except:
    # TODO:Done on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: Done insert form data as a new Venue record in the db, instead
  # TODO: Done modify data to be the data object returned from db insertion
  form = ArtistForm(request.form, meta={"csrf": False})

  try:
    # get all of the data
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website = form.website.data
    image_link = form.image_link.data

    seeking_venue = False
    if 'seeking_venue' in request.form:
      seeking_venue = True

    seeking_description = form.seeking_description.data

    if form.validate():
      # define artist from entered data and add it to db
      artist = Artist(name=name, city=city, state=state,
                    phone=phone, genres=genres, facebook_link=facebook_link,
                    website=website, image_link=image_link,
                    seeking_venue=seeking_venue,
                    seeking_description=seeking_description)
      db.session.add(artist)
      db.session.commit()
      # TODO:Done on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')      
    else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')     
      flash_errors(form)
  except:
    # TODO:Done on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()


  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO:Done replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
     
  data = []

  venues = Venue.query.all()

  for venue in venues:
    for show in venue.shows:
      data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO:Done insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)

  try:
    # get all of the data
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    # define venue from entered data and add it to db
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
    
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # TODO:Done on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()

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