from flask import url_for
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from datetime import datetime, timezone
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class TimeStampAPIMixin(object):
    date_created: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc), nullable=False)
    date_modifeid: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc), nullable=True, onupdate=datetime.now(timezone.utc))

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page, error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page, **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page, 
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class User(PaginatedAPIMixin, TimeStampAPIMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(20), index=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(20), index=True, nullable=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(120), index=True)
    #date_created: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(240), nullable=True)
    token: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    token_expiration: so.Mapped[datetime]
    followers: so.WriteOnlyMapped['User'] = so.relationship(secondary=followers, primaryjoin=followers.c.followers_id, 
                                                            secondaryjoin=followers.c.followed_id, back_populates="followers")
    following: so.WriteOnlyMapped['User'] = so.relationship(secondary=followers, primaryjoin=followers.c.followed_id, 
                                                            secondaryjoin=followers.c.followers_id, back_populates='following')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'date_created': self.date_created,
            'date_modified': self.date_modifeid
        }
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.password_hash=generate_password_hash(data['password'])

    def is_following(self, user):
        return self.following.select(User).where(User.username == user.id) is not None

    def follow(self, user):
        if not self.is_following(user):
            return self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            return self.following.remove(user)

    def is_follower(self, user):
        return self.followers.select(User).where(User.id == user.id) is not None
        
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)
    
    def following_count(self):
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)

followers = db.Table(
    "followers",
    sa.Column('followers_id', sa.ForeignKey(User.id), primary_key=True),
    sa.Column('followed_id', sa.ForeignKey(User.id), primary_key=True)
)