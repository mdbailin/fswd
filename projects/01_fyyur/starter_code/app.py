#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
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


# TODO: connect to a local postgresql database
# SOLVED: SQLALCHEMY_DATABASE_URI = 'postgresql://matthewbailin@localhost:5432/fyyur'

#----------------------------------------------------------------------------#
# Functions
#-----------------------------------------------------------------
#-----------#

def past_shows(shows):
  past_shows_info = []

  for show in shows:
    if show.start_time <= datetime.now():
      show_artist = Artist.query.filter_by(id=show.artist_id).first()
      past_shows_info.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist_name,
        "artist_image_link": show.artist.image_link,
        "venue_id": show.venue_id,
        "venue_name": show.venue_name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

    return past_shows_info

def upcoming_shows(shows):
  upcoming_shows_info = []

  for show in shows:
    if show.start_time > datetime.now():
      show_artist = Artist.query.filter_by(id=show.artist_id).first()
      upcoming_shows_info.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist_name,
        "artist_image_link": show.artist.image_link,
        "venue_id": show.venue_id,
        "venue_name": show.venue_name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
  
  return upcoming_shows_info

def flash_errors(form):
  """Flashes form errors"""
  for field, errors in form.errors.items():
    for error in errors:
      flash(u"Error in the %s field - %s" % (
        getattr(form, field).label.text,error), 'error'
      )

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  #create variable to store all of the venue variables
  data = []
  #get current time
  current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')
  #gather all areas
  all_areas = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  for area in all_areas:
    #find all venues in a city/state area
    area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    #store data of each venue in a new variable
    venue_info = []
    for venue in area_venues:
      upcoming_shows = Show.query.filter_by(venue_id=venue.id).all()
      venue_info.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      })
    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venue_info
    })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  print("Searching now...")
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()
  #create response to store results of search
  response={
    "count": len(venues),
    "data": []
  }
  #append each of the found venues to the response
  for venue in venues:
    response["data"].append({
      "id": venue.id,
      "name": venue.name
    })
  #return results of the search
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  #SOLVED: query venue and shows by venue id, then populate data

  venue = Venue.query.filter_by(id=venue_id).first()
  shows = Show.query.filter_by(venue_id=venue_id).all()
  previous_shows = past_shows(shows)
  next_shows = upcoming_shows(shows)

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
    "past_shows": venue.past_shows,
    "upcoming_shows": venue.upcoming_shows,
    "past_shows_count": len(previous_shows),
    "upcoming_shows_count": len(next_shows)
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
    # retrieve all data from the form
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
      # define new venue instance and append to db
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
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')     
      flash_errors(form)

  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()


  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    venue_name = venue.name
    db.session.delete(venue)
    db.session.commit()
    flash('The Venue ' + venue_id + ' ' + venue_name + ' has been successfully deleted.')
  except:
    db.session.rollback()
    flash('Delete was unsuccessful. Please try again.')
  finally:
    db.session.close()
  
  return jsonify({'success': True})


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  #SOLVED: query all artists with Artist.query.all()

  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  #SOLVED: query filter artists using ilike, create a response JSON to store the data, append data with
  # artist id and name.
  
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  response ={
    "count": len(artists),
    "data": []
  }
  for artist in artists:
    response["data"].append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.filter_by(id=artist_id).first()
  shows = Show.query.filter_by(artist_id=artist_id).all()
  previous_shows = past_shows(shows)
  next_shows = upcoming_shows(shows)

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
    "past_shows": previous_shows,
    "upcoming_shows": next_shows,
    "past_show_count": len(previous_shows),
    "upcoming_show_count": len(next_shows)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  form = ArtistForm(obj=artist)
  edit_artist={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genre,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  #SOLVED: define a current artist by artist_id, then replace artist JSON with edit_artist JSON for the artist_id
  return render_template('forms/edit_artist.html', form=form, artist=edit_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form, meta={'csrf': False})

  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    #get all of the data
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
      #define newly edited artist instance and insert into db
      artist = Artist(name=artist.name, city=artist.city, state=artist.state,
                      phone=artist.phone, genres=artist.genres, facebook_link=artist.facebook_link,
                      website=artist.website, image_link=artist.image_link,
                      seeking_venue=artist.seeking_venue, seeking_description=artist.seeking_description)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated.')
  
    else:
      flash('An error occurred. The artist currently known as ' + request.form['name'] + ' was not succesfully updated.')
      flash_errors(form)
  
  except:
    #If db insert unsuccessful, flash an error message and rollback
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    db.session.rollback()
  
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  form = VenueForm(obj=venue)
  
  edit_venue = {
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
  # TODO: populate form with values from venue with ID <venue_id>
  # SOLVED: replaces data of venue with edit_venue, then redirects to use edit_venue data
  return render_template('forms/edit_venue.html', form=form, venue=edit_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  # SOLVED: grabs data from form, then edits venue record with data
  form = VenueForm(request.form, meta={'csrf': False})

  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    #get all of the data from the form
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
      #define new venue instance and insert into db
      venue = Venue(name=venue.name, city=venue.city, state=venue.state,
                    address=venue.address, phone=venue.phone, genres=venue.genres,
                    facebook_link=venue.facebook_link, website=venue.website,
                    image_link=venue.image_link, seeking_talent=venue.seeking_talent,
                    seeking_description=venue.seeking_description)
      db.session.commit()

      flash('Venue ' + request.form['name'] + ' was successfully updated.')
    
    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' was not updated.')
      flash_errors(form)
  
  except:
    flash('An error occured. Venue ' + request.form['name'] + ' could not be updated.')
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
      # define new artist instance and insert to db
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
  # TODO: replace with real venues data.
  data = []

  venues = Venue.query.all()
  for venue in venues:
    for show in venue.shows:
      data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link
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

    # define new show instance and insert to db
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
