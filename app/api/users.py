from flask import request, url_for
from app.api import bp as api_bp
from app.api.errors import bad_request
from app import db
import sqlalchemy as sa
from app.models import User

@api_bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    return db.get_or_404(User, id).to_dict()

@api_bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.get_or_404(User, id)
    data = request.get_json()
    if 'username' in data and data['username'] != user.username and db.session.scalar(sa.select(User).where(User.username == data['username'])):
        return bad_request('Please, use a different username')
    if 'email' in data and data['email'] != user.email and db.session.scalar(sa.select(User).where(User.email == data['email'])):
        return bad_request('Please, use a different username')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return user.to_dict()


@api_bp.route('/users', methods=['GET'])
def get_users():
    page=request.args.get('page', 1, type=int)
    per_page=min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(sa.select(User), page, per_page, 'api.get_users')


@api_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('Please, provide username, email and password')
    if db.session.scalar(sa.select(User).where(User.username == data['username'])):
        return bad_request('Username already exist, please, use a different one')
    if db.session.scalar(sa.select(User).where(User.email == data['email'])):
        return bad_request('email already exist, please, use a different one')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201, {'Location': url_for('api.get_user', id=user.id)}
