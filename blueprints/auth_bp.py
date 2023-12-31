from flask import Blueprint
from flask import abort
from flask_jwt_extended import create_access_token, get_jwt_identity
from init import db,bcrypt
from models.user import User, UserSchema
from flask import request
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def users_register(): 
  try:
    # to validate and sanitize all the incoming data via Marshmallow schema
    # Parse, sanitize and validate the incoming JSON data
    # via schema
    user_info = UserSchema().load(request.json)
    # Create a new User instance with the schema data
    user = User(
      email=user_info['email'],
      password=bcrypt.generate_password_hash(user_info['password']).decode('utf8'),
      name=user_info['name'],
      last_name=user_info['last_name']
    )
    # Add and commit the new user
    db.session.add(user)
    db.session.commit()
    
    # Return the new user, excluding the password
    return UserSchema(exclude=['password']).dump(user), 201
  except IntegrityError:
    return {'error': 'Email address already in use'}, 409
  
@auth_bp.route('/login', methods=['POST'])
def users_login():
  try:
    # to get the user from the database, where email equals to the email from the user data posted
    stmt = db.select(User).filter_by(email=request.json['email'])
    #  returning one result (scalar method, not scalars)
    user = db.session.scalar(stmt)
    # checking if the user exists (user=True) and password is correct,
    # first parameter is users password from database,
    # the second one is the one retrieved from the POST method)
    if user and bcrypt.check_password_hash(user.password, request.json['password']):
      # generating a token for the user
      token = create_access_token(identity=user.id, expires_delta = timedelta(hours=2))
      return {'token': token, 'user': UserSchema(exclude=['password']).dump(user)}
    else:
      return {'error': 'Invalid email address or password'}, 401
  except KeyError:
    return{'error': 'Email and password are required'}, 400


def owner_required():
  user_id = get_jwt_identity()
  stmt = db.select(User).filter_by(id=user_id)
  user = db.session.scalar(stmt)
  if not user and user.is_owner:
    abort(401, description='You must be a store owner')
  
  
# Matching the user id with the user id on the review
def author_required(author_id):
  user_id = get_jwt_identity()
  stmt = db.select(User).filter_by(id=user_id)
  user = db.session.scalar(stmt)
  if not user.id == author_id:
    abort(401)

def get_access(stores):
  user_id = get_jwt_identity()
  stmt = db.select(User).filter_by(id=user_id)
  user = db.session.scalar(stmt)
  if not user.is_owner and stores != user.store.id:
    abort(401)

