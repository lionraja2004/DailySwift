from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_pyfile('config.py')

app.config['SECRET_KEY'] = 'your-secret-key-here'  # Your key
print("SECRET KEY IS:", app.config['SECRET_KEY'])  # Debug line
# Initialize SQLAlchemy with explicit configuration
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Database Models with explicit column definitions
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    user_type = Column(String(20), nullable=False)  # 'seeker' or 'poster'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship('Job', backref='poster')
    applications = relationship('Application', backref='seeker')
    sent_messages = relationship('Message', foreign_keys='Message.sender_id', backref='sender')
    received_messages = relationship('Message', foreign_keys='Message.receiver_id', backref='receiver')
    given_reviews = relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer')
    reviews = relationship('Review', foreign_keys='Review.reviewee_id', backref='reviewee')

class Job(db.Model):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    pay = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    duration = Column(String(50), nullable=False)
    requirements = Column(Text, nullable=False)
    poster_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    applications = relationship('Application', backref='job')

class Application(db.Model):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    seeker_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reviewee_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Routes (keep all your existing route functions exactly as they were)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, user_type=user_type).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            return redirect(url_for(f'{user_type}_dashboard'))
        
        return render_template('auth/login.html', error='Invalid credentials', user_type=user_type)
    
    return render_template('auth/login.html', user_type=user_type)

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            return render_template('auth/register.html', error='Username already exists', user_type=user_type)
        
        if User.query.filter_by(email=email).first():
            return render_template('auth/register.html', error='Email already exists', user_type=user_type)
        
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            user_type=user_type
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session['user_type'] = new_user.user_type
        return redirect(url_for(f'{user_type}_dashboard'))
    
    return render_template('auth/register.html', user_type=user_type)

@app.route('/seeker/dashboard')
def seeker_dashboard():
    if 'user_id' not in session or session['user_type'] != 'seeker':
        return redirect(url_for('login', user_type='seeker'))
    
    jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    return render_template('seeker/dashboard.html', jobs=jobs)

@app.route('/poster/dashboard')
def poster_dashboard():
    if 'user_id' not in session or session['user_type'] != 'poster':
        return redirect(url_for('login', user_type='poster'))
    
    jobs = Job.query.filter_by(poster_id=session['user_id']).order_by(Job.created_at.desc()).all()
    return render_template('poster/dashboard.html', jobs=jobs)

@app.route('/poster/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'poster':
        return redirect(url_for('login', user_type='poster'))
    
    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            description=request.form['description'],
            pay=request.form['pay'],
            location=request.form['location'],
            duration=request.form['duration'],
            requirements=request.form['requirements'],
            poster_id=session['user_id']
        )
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('poster_dashboard'))
    
    return render_template('poster/post_job.html')

@app.route('/seeker/jobs')
def seeker_jobs():
    if 'user_id' not in session or session['user_type'] != 'seeker':
        return redirect(url_for('login', user_type='seeker'))
    
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('seeker/jobs.html', jobs=jobs)

@app.route('/seeker/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'seeker':
        return redirect(url_for('login', user_type='seeker'))
    
    existing_application = Application.query.filter_by(job_id=job_id, seeker_id=session['user_id']).first()
    
    if not existing_application:
        application = Application(
            job_id=job_id,
            seeker_id=session['user_id'],
            status='pending'
        )
        db.session.add(application)
        db.session.commit()
    
    return redirect(url_for('seeker_applications'))

@app.route('/seeker/applications')
def seeker_applications():
    if 'user_id' not in session or session['user_type'] != 'seeker':
        return redirect(url_for('login', user_type='seeker'))
    
    applications = Application.query.filter_by(seeker_id=session['user_id']).all()
    return render_template('seeker/applications.html', applications=applications)

@app.route('/poster/applications/<int:job_id>')
def poster_applications(job_id):
    if 'user_id' not in session or session['user_type'] != 'poster':
        return redirect(url_for('login', user_type='poster'))
    
    job = Job.query.get_or_404(job_id)
    if job.poster_id != session['user_id']:
        return redirect(url_for('poster_dashboard'))
    
    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('poster/applications.html', job=job, applications=applications)

@app.route('/poster/update-application/<int:app_id>', methods=['POST'])
def update_application(app_id):
    if 'user_id' not in session or session['user_type'] != 'poster':
        return redirect(url_for('login', user_type='poster'))
    
    application = Application.query.get_or_404(app_id)
    job = Job.query.get_or_404(application.job_id)
    
    if job.poster_id != session['user_id']:
        return redirect(url_for('poster_dashboard'))
    
    application.status = request.form['status']
    db.session.commit()
    
    return redirect(url_for('poster_applications', job_id=job.id))

# Chat functionality
@app.route('/chat/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    other_user = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        ((Message.sender_id == session['user_id']) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == session['user_id']))
    ).order_by(Message.created_at).all()
    
    return render_template('chat.html', other_user=other_user, messages=messages)

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = session['user_id']
    receiver_id = data['receiver_id']
    content = data['content']
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    emit('receive_message', {
        'sender_id': sender_id,
        'content': content,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }, room=f'user_{receiver_id}')

# Reviews
@app.route('/review/<int:user_id>', methods=['GET', 'POST'])
def review(user_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    reviewee = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        review = Review(
            reviewer_id=session['user_id'],
            reviewee_id=user_id,
            rating=int(request.form['rating']),
            comment=request.form.get('comment', '')
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('user_profile', user_id=user_id))
    
    return render_template('review.html', reviewee=reviewee)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter_by(reviewee_id=user_id).all()
    return render_template('profile.html', user=user, reviews=reviews)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=True)
    