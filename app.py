from flask import Flask, jsonify, request 
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from functools import wraps
import jwt


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkennwort'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookd5.db'
app.config['TESTING'] = True
app.config.from_object(__name__)

db = SQLAlchemy(app)

CORS(app, resources={r"/*":{'origins':"*"}})
# CORS(app, resources={r'/*':{'origins': 'http://localhost:8081',"allow_headers": "Access-Control-Allow-Origin"}})


## --------------------------------------------------------------###

class Users(db.Model, UserMixin):
    userid = db.Column(db.Integer(), primary_key=True)
    user_email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(15), nullable=False)
    username = db.Column(db.String(15), nullable=False)
    user_role = db.Column(db.String(10))
    created = db.Column(db.DateTime, nullable=False)
    lastlogin = db.Column(db.DateTime, nullable=False)
    lastbooked = db.Column(db.DateTime, nullable=True)


    def __repr__(self):
        return "User %r" % self.userid

## --------------------------------------------------------------###

class Venues(db.Model):
	venue_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
	venue_name = db.Column(db.String(30), nullable=False)
	venue_place = db.Column(db.String(30), nullable=False)
	venue_location = db.Column(db.String(30), nullable=False)
	venue_capacity = db.Column(db.Integer(), nullable=False)
	shows = db.relationship("Shows",
							back_populates="venues",
							cascade="all, delete")

	def __repr__(self):
		return f'Venue {self.venue_id}'

## --------------------------------------------------------------###
class Shows(db.Model):
	show_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
	show_name = db.Column(db.String(30), nullable=False)
	show_time = db.Column(db.String(30), nullable=False)
	show_tag = db.Column(db.String(30), nullable=False)
	show_rating = db.Column(db.Integer(), nullable=False)
	show_tickets = db.Column(db.Integer(), nullable=False)
	show_price = db.Column(db.Integer(), nullable=False)
	show_venue_id = db.Column(db.Integer(),
								db.ForeignKey('venues.venue_id',
											ondelete="CASCADE"),
								nullable=False)
	venues = db.relationship("Venues", back_populates="shows")

	def __repr__(self):
		return f'Show {self.show_id}'

## --------------------------------------------------------------###

class Bookings(db.Model):
	booking_id = db.Column(db.Integer(), primary_key=True)
	booking_userid = db.Column(db.Integer(), db.ForeignKey('users.userid'))
	booking_venue_id = db.Column(db.Integer(), db.ForeignKey('venues.venue_id'))
	booking_venue_name = db.Column(db.Integer(), db.ForeignKey('venues.venue_name'))
	booking_venue_place = db.Column(db.Integer(), db.ForeignKey('venues.venue_place'))
	booking_venue_location = db.Column(db.Integer(), db.ForeignKey('venues.venue_location'))
	booking_show_id = db.Column(
		db.Integer(), db.ForeignKey('shows.show_id', ondelete="CASCADE"))
	booking_show_name = db.Column(db.String(30), db.ForeignKey('shows.show_name'))
	booking_show_time = db.Column(db.String(30), db.ForeignKey('shows.show_time'))
	booking_show_tag = db.Column(db.String(30), db.ForeignKey('shows.show_tag'))
	booking_tickets = db.Column(db.Integer(), nullable=False)
	booking_price = db.Column(db.Integer(), db.ForeignKey('shows.show_price'))
	booking_total_price = db.Column(db.Integer(), nullable=False)
	booking_show_rating = db.Column(db.Integer(), nullable=False)
	booking_rating = db.Column(db.Integer(), nullable=True)
	booking_created = db.Column(db.DateTime, nullable=False)


	def __repr__(self):
		return f'Booking {self.booking_id}'

## --------------------------------------------------------------###

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print("request : ", request)
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is Missing'})
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = Users.query.filter_by(user_email = data['useremail']).first()
        except Exception as e:
            return jsonify({'message':'Token is Invalid'})
        
        return f(current_user, *args, **kwargs)
    return decorated
            
                
## --------------------------------------------------------------###
@app.route('/', methods=['GET'])
def home():
    return("Book Tickets for your Favourite Shows!")

## --------------------------------------------------------------###

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        post_data = request.get_json()
        if Users.query.filter_by(user_email=post_data['email']).first():
            return {'message': 'Account with this Email already Exists. Please Login.'}
        else:
            if post_data['admin']:
                user = Users(username=post_data['username'], password=post_data['password'], user_email=post_data['email'], user_role='admin', created=datetime.now(), lastlogin=datetime.now())
                db.session.add(user)
            elif not post_data['admin']:
                user = Users(username=post_data['username'], password=post_data['password'], user_email=post_data['email'], user_role='user', created=datetime.now(), lastlogin=datetime.now())
                db.session.add(user)
            db.session.commit()
            return {'message': 'success'}

## --------------------------------------------------------------###
@app.route('/login/admin', methods=['POST'])
@app.route('/login/user', methods=['POST'])
def login():
    if request.method == 'POST':
        role = None
        if request.path == '/login/user':
            role = 'user'
        elif request.path == '/login/admin':
            role = 'admin'
        post_data = request.authorization        
        user = Users.query.filter_by(user_email = post_data.username).first()
        if not user:
            return {'message': 'Login Failed. User not found'}
        else:
            if user.password == post_data.password:
                token = jwt.encode({'username': user.username, 'useremail': user.user_email, 'lastlogin': user.lastlogin.strftime('%d-%m-%Y %H:%M:%S'),'role':role, 'exp': datetime.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])
                print(token)
                user.lastlogin = datetime.now()
                db.session.commit()
                return jsonify({'token': token, 'message': 'success'})
        return {'message' : 'Login Failed. Check Password'}
            

## --------------------------------------------------------------###
@app.route('/venues', methods=['GET'])
def get_all_venues():
    if request.method == 'GET':
        venues = Venues.query.all()
        output = []
        for venue in venues:
            venue_data = {}
            venue_data['id'] = venue.venue_id
            venue_data['name'] = venue.venue_name
            venue_data['place'] = venue.venue_place
            venue_data['location'] = venue.venue_location
            venue_data['capacity'] = venue.venue_capacity
            output.append(venue_data)
        return jsonify({'venues' : output})


@app.route('/venues', methods=['POST'])
@token_required
def create_venue(current_user):
	if current_user.user_role == 'admin':
		post_data = request.get_json()
		venue = Venues(venue_name=post_data['name'], venue_place=post_data['place'], venue_location=post_data['location'], venue_capacity=int(post_data['capacity']))
		db.session.add(venue)
		db.session.commit()
		return {'message': 'success'}
	else:
		return {'message': 'failed. login as Admin'}
    

@app.route('/venues/<venueid>', methods=['PUT'])
@token_required
def edit_venue(current_user, venueid):
    if current_user.user_role == 'admin':
        post_data = request.get_json()
        venue = Venues.query.filter_by(venue_id=venueid).first()
        venue.venue_name = post_data['name']
        venue.venue_place = post_data['place']
        venue.venue_location = post_data['location']
        venue.venue_capacity = post_data['capacity']
        db.session.commit()
        return {'message': 'success'}
    else:
        return {'message': 'failed. login as Admin'}


@app.route('/venues/<venueid>', methods=['DELETE'])
@token_required
def delete_venue(current_user, venueid):
    if current_user.user_role == 'admin':
        venue = Venues.query.filter_by(venue_id = venueid).delete()
        shows = Shows.query.filter_by(show_venue_id=venueid).delete()
        db.session.commit()
        return {'message': 'success'}
    else:
        return {'message': 'failed. login as Admin'}


## --------------------------------------------------------------###

@app.route('/shows', methods=['POST'])
@token_required
def create_show(current_user):
    if current_user.user_role == 'admin':
        post_data = request.get_json()
        show = Shows(show_name=post_data['name'], show_time=post_data['time'], show_tag=post_data['tag'], show_rating=int(post_data['rating']), show_tickets=post_data['tickets'], show_price=post_data['price'], show_venue_id=post_data['venue'])
        db.session.add(show)
        db.session.commit()
        return {'message': 'success'}
    else:
        return {'message': 'failed. login as Admin'}


@app.route('/shows/<showid>', methods=['DELETE'])
@token_required
def delete_show(current_user, showid):
    if current_user.user_role == 'admin':
        show = Shows.query.filter_by(show_id = showid).delete()
        db.session.commit()
        return {'message': 'success'}
    else:
        return {'message': 'failed. login as Admin'}


@app.route('/shows/<showid>', methods=['PUT'])
@token_required
def edit_show(current_user, showid):
	if current_user.user_role == 'admin':
		post_data = request.get_json()
		show = Shows.query.filter_by(show_id=showid).first()
		show.show_name = post_data['name']
		show.show_time = post_data['time']
		show.show_tag = post_data['tag']
		show.show_rating = post_data['rating']
		show.show_tickets = post_data['tickets']
		show.show_price = post_data['price']
		show.show_venue_id = post_data['venue']
		db.session.commit()
		return {'message': 'success'}
	else:
		return {'message': 'failed. login as Admin'}


@app.route('/shows/<venue_id>', methods = ['GET'])
def get_show_by_venue(venue_id):
    if request.method == 'GET':
        shows = Shows.query.filter_by(show_venue_id=venue_id).all()
        output = []
        for show in shows:
            show_data = {}
            show_data['id'] = show.show_id
            show_data['name'] = show.show_name
            show_data['time'] = show.show_time
            show_data['tag'] = show.show_tag
            show_data['rating'] = show.show_rating
            show_data['tickets'] = show.show_tickets
            show_data['price'] = show.show_price
            show_data['venue_id'] = show.show_venue_id
            output.append(show_data)
        return jsonify({'shows' : output})
    

@app.route('/bookings', methods=['POST'])
@token_required
def book_show(current_user):
    if current_user.user_role == 'user':
        post_data = request.get_json()
        booking = Bookings(booking_userid=current_user.userid, booking_venue_id=post_data['venueid'], booking_show_id=post_data['showid'], booking_tickets=int(post_data['tickets']), booking_price=post_data['price'], booking_total_price=int(post_data['price']*post_data['tickets']), booking_show_rating=post_data['rating'], booking_show_name=post_data['showname'], booking_show_time=post_data['showtime'], booking_show_tag=post_data['showtag'], booking_venue_name=post_data['venuename'],booking_venue_place=post_data['venueplace'], booking_venue_location=post_data['venuelocation'], booking_created=datetime.now())
        available_seats = get_available_tickets_dict()
        if booking.booking_tickets <= available_seats[(booking.booking_show_id)]:
            current_user.lastbooked = datetime.now()
            db.session.add(booking)
            db.session.commit()
        else:
            return {'message':'failed', 'reason': 'Sorry. Check Available Tickets and Retry.'}
        return {'message': 'success'}
    else:
        return {'message': 'failed. login as User'}
    

@app.route('/bookings/', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    print(current_user)
    if current_user.user_role == 'user':
        output = []
        bookings = Bookings.query.filter_by(booking_userid = current_user.userid)
        for booking in bookings:
            booking_dict = {}
            booking_dict['booking_id'] = booking.booking_id
            booking_dict['venue_name'] = booking.booking_venue_name
            booking_dict['venue_place'] = booking.booking_venue_place
            booking_dict['venue_location'] = booking.booking_venue_location
            booking_dict['show_name'] = booking.booking_show_name
            booking_dict['show_time'] = booking.booking_show_time
            booking_dict['show_tag'] = booking.booking_show_tag
            booking_dict['tickets'] = booking.booking_tickets
            booking_dict['price'] = booking.booking_price
            booking_dict['show_rating'] = booking.booking_show_rating
            booking_dict['user_rating'] = booking.booking_rating
            
            output.append(booking_dict)
        return jsonify({'message': 'success', 'bookings': output})
            
    else:
        return {'message': 'failed. login as User'}

@app.route('/bookings/<bid>', methods=['PUT'])
@token_required
def rate_booking(current_user, bid):
    if current_user.user_role == 'user':
        booking = Bookings.query.filter_by(booking_id=bid).first()
        if booking:
            booking.booking_rating = request.get_json()['rating']
            db.session.commit()
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'failed', 'reason': 'booking not found'})
    else:
        return jsonify({'message':'failed. login as user'})


@app.route('/tickets', methods=['GET'])
def get_available_tickets():
    output = {}
    shows = Shows.query.all()
    for show in shows:
        output[show.show_id] = show.show_tickets
        bookings = Bookings.query.filter_by(booking_show_id=show.show_id).all()
        if bookings:
        	for booking in bookings:
                    output[show.show_id] -= booking.booking_tickets
    return jsonify({'message': 'success', 'available': output})
            

def get_available_tickets_dict():
    output = {}
    shows = Shows.query.all()
    for show in shows:
        output[show.show_id] = show.show_tickets
        bookings = Bookings.query.filter_by(booking_show_id=show.show_id).all()
        if bookings:
        	for booking in bookings:
                    output[show.show_id] -= booking.booking_tickets
    return output


# @app.route('/admin/dashboard', methods=['POST', 'GET'])
# def admin_dashboard():
#     return {'message': 'admin dashboard from flask'}


# ## --------------------------------------------------------------###

# @app.route('/user/dashboard', methods=['POST', 'GET'])
# def user_dashboard():
#     return {'message': 'user dashboard from flask'}

# ## --------------------------------------------------------------###

# @app.route('/user/bookings', methods=['POST', 'GET'])
# def bookings():
#     return {'message': 'user booking from flask'}

# ## --------------------------------------------------------------###
# @app.route('/user/profile', methods=['POST', 'GET'])
# def profile():
#     return {'message': 'user profile from flask'}

# ## --------------------------------------------------------------###
# @app.route('/admin/summary', methods=['GET'])
# def summary():
#     return {'message': 'admin summary from flask'}


## --------------------------------------------------------------###

if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)
