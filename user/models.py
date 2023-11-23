from db import db

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(200), nullable=False)
    tweets = db.relationship('Tweet', backref='user', lazy=True)

    following = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    def follow(self, user):
        if user.id == self.id:
            return False

        if not self.is_following(user):
            self.following.append(user)
            return True
        return False

    def unfollow(self, user):
        if user.id == self.id:
            return False

        if self.is_following(user):
            self.following.remove(user)
            return True
        return False

    def is_following(self, user):
        return self.following.filter(followers.c.followed_id == user.id).count() > 0