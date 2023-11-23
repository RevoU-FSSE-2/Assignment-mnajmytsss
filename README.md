# Week 12 - Creates twitter-like back-end using Flask

## Features:

- Login / Register

- See profile; user id, username, bio, number of following and followers, 10 recent tweets

- Post tweet

- Follow / unfollow someone based on their user id

## How to use:

1. Pull the project (in case I cant deploy it)

2. Uncomment this line of code on app.py to initialize database (shouldn't need to since its connected to my database, which contains necesssary column)

```python
# with app.app_context():
#     db_init()
```
3. Import the Postman collection data (should be in the root folder)

## Models:

### User & Follow:

```python
from db import db
from enum import Enum
from sqlalchemy import Enum as EnumType
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

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

```

### Tweet:

```python
from db import db

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    tweet = db.Column(db.String(150), nullable=False)
    published_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

```

## List of important codes:

### Registration:

```python
    existing_user = User.query.filter_by(username=data['username']).first()

    if existing_user:
        return {"error": "username sudah digunakan"}, 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password, bio=data['bio'])
    db.session.add(new_user)
    db.session.commit()

    return {
        'id': new_user.id,
        'username': new_user.username,
        'bio': new_user.bio
    }
```

### Login:

```python
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"error": "username atau password tidak tepat"}, 400
    
    valid_password = bcrypt.check_password_hash(user.password, password)
    if not valid_password:
        return {"error": "username atau password tidak tepat"}, 400
    
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(minutes=10)
    }
    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm="HS256")
    
    return {
        'id': user.id,
        'username': user.username,
        'token': token
    }
```

### Get Profile:

```python
    payload = decode_jwt(token)
    print("Decoded Payload:", payload)

    if not payload:
        return {"error": "Token tidak valid"}, 401

    user_id = payload.get("user_id")

    if not user_id:
        return {"error": "User ID tidak ditemukan"}, 401

    user = User.query.get(user_id)

    if not user:
        return {"error": "User tidak ditemukan!"}, 404

    tweets = Tweet.query.filter_by(user_id=user_id).order_by(Tweet.published_at.desc()).limit(10).all()

    following_count = user.following.count()
    followers_count = user.followers.count()
    tweet_details = [
        {
            'id': tweet.id,
            'published_at': tweet.published_at,
            'tweet': tweet.tweet
        }
        for tweet in tweets
    ]

    return {
        'id': user.id,
        'username': user.username,
        'bio': user.bio,
        'following_count': following_count,
        'followers_count': followers_count,
        'tweets': tweet_details
    }
```

### Post Tweet:

```python
    payload = decode_jwt(token) 
    print("Decoded Payload:", payload)

    if not payload or 'user_id' not in payload:
        return {"error": "Token tidak valid"}, 401

    user_id = payload['user_id']

    try:
        data = TweetSchema().load(request.get_json())
    except ValidationError as err:
        return {"error": err.messages}, 400

    tweet = data.get("tweet")

    if not tweet or len(tweet) > 150:
        return {"error": "Tweet tidak boleh lebih dari 150 karakter"}, 400

    new_tweet = Tweet(user_id=user_id, tweet=tweet)
    db.session.add(new_tweet)
    db.session.commit()

    return jsonify({
        'id': new_tweet.id,
        'published_at': new_tweet.published_at.isoformat(),
        'tweet': new_tweet.tweet
    }), 200
```

### Following User:

```python
    payload = decode_jwt(token) 
    print("Decoded Payload:", payload)

    if not payload:
        return {"error": "Token tidak valid"}, 401

    current_user_id = payload.get("user_id")

    if not current_user_id:
        return {"error": "User ID tidak ditemukan didalam token"}, 401

    current_user = User.query.get(current_user_id)
    user_to_follow = User.query.get(user_id)

    if not current_user or not user_to_follow:
        return {"error": "User tidak ditemukan!"}, 404
    
    if current_user_id == user_id:
        return {"error": "tidak bisa follow diri sendiri"}, 400

    if current_user.follow(user_to_follow):
        db.session.commit()
        return {"message": f"kamu memfollow {user_to_follow.username}"}

    return {"message": "kamu telah memfollow user ini"}
```

### Unfollowing User:

```python
    payload = decode_jwt(token) 
    print("Decoded Payload:", payload)

    if not payload:
        return {"error": "Token tidak valid"}, 401

    current_user_id = payload.get("user_id")

    if not current_user_id:
        return {"error": "User ID not found in token"}, 401

    current_user = User.query.get(current_user_id)
    user_to_unfollow = User.query.get(user_id)

    if not current_user or not user_to_unfollow:
        return {"error": "User not found!"}, 404
    
    if current_user_id == user_id:
        return {"error": "You are not following yourself"}, 400

    if current_user.unfollow(user_to_unfollow):
        db.session.commit()
        return {"message": f"You have unfollowed {user_to_unfollow.username}"}

    return {"message": "You were not following this user"}
```

here's the .env file 

```
DATABASE_URL = "postgresql://postgres:Smandak123!@db.mjkouqmjrruzrcgmakws.supabase.co:5432/postgres"
SECRET_KEY = "RAHASIADONG"

```
