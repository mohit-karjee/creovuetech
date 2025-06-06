from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Text

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(Text)
    creator_type = db.Column(db.String(50))  # artist, writer, filmmaker, musician, etc.
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    owned_circles = db.relationship('Circle', backref='owner', lazy=True, foreign_keys='Circle.owner_id')
    circle_memberships = db.relationship('CircleMembership', backref='user', lazy=True)
    projects = db.relationship('Project', backref='creator', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Circle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # film, music, art, writing, etc.
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_members = db.Column(db.Integer, default=10)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = db.relationship('CircleMembership', backref='circle', lazy=True, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='circle', lazy=True)
    
    @property
    def member_count(self):
        return len(self.memberships)
    
    @property
    def members(self):
        return [membership.user for membership in self.memberships]
    
    def __repr__(self):
        return f'<Circle {self.name}>'

class CircleMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey('circle.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # owner, admin, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'circle_id'),)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey('circle.id'), nullable=True)
    
    # Funding details
    funding_goal = db.Column(db.Float, default=0.0)
    current_funding = db.Column(db.Float, default=0.0)
    funding_deadline = db.Column(db.DateTime)
    
    # Project status
    status = db.Column(db.String(20), default='planning')  # planning, funding, production, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    milestones = db.relationship('ProjectMilestone', backref='project', lazy=True, cascade='all, delete-orphan')
    
    @property
    def funding_percentage(self):
        if self.funding_goal > 0:
            return min(100, (self.current_funding / self.funding_goal) * 100)
        return 0
    
    @property
    def days_remaining(self):
        if self.funding_deadline:
            delta = self.funding_deadline - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    def __repr__(self):
        return f'<Project {self.title}>'

class ProjectMilestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    target_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Milestone {self.title}>'

class MediaHouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(Text)
    industry = db.Column(db.String(100))  # streaming, tv, film, music, etc.
    website = db.Column(db.String(200))
    contact_email = db.Column(db.String(120))
    logo_url = db.Column(db.String(300))
    investment_range_min = db.Column(db.Float, default=0)
    investment_range_max = db.Column(db.Float, default=0)
    preferred_categories = db.Column(db.String(500))  # comma-separated list
    investment_criteria = db.Column(Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    investments = db.relationship('MediaHouseInvestment', backref='media_house', lazy=True)
    
    def __repr__(self):
        return f'<MediaHouse {self.name}>'

class MediaHouseInvestment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_house_id = db.Column(db.Integer, db.ForeignKey('media_house.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    investment_type = db.Column(db.String(50), default='equity')  # equity, revenue_share, licensing
    terms = db.Column(Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    investment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='media_investments')

class AIAssistanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    request_type = db.Column(db.String(50), nullable=False)  # budget_planning, script_draft, marketing_strategy, etc.
    description = db.Column(Text, nullable=False)
    ai_response = db.Column(Text)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_requests')
    project = db.relationship('Project', backref='ai_requests')
    
    def __repr__(self):
        return f'<AIAssistanceRequest {self.request_type}>'

class FundingContribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    contributor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be anonymous
    amount = db.Column(db.Float, nullable=False)
    contributor_type = db.Column(db.String(20), default='community')  # community, media_house
    contribution_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='contributions')
    contributor = db.relationship('User', backref='contributions')

class Pitch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    media_house_id = db.Column(db.Integer, db.ForeignKey('media_house.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pitch_text = db.Column(Text, nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, accepted, rejected
    pitch_date = db.Column(db.DateTime, default=datetime.utcnow)
    response_date = db.Column(db.DateTime)
    media_house_response = db.Column(Text)
    
    # Relationships
    project = db.relationship('Project', backref='pitches')
    media_house = db.relationship('MediaHouse', backref='received_pitches')
    creator = db.relationship('User', backref='sent_pitches')
    
    def __repr__(self):
        return f'<Pitch {self.project.title} to {self.media_house.name}>'

class Publication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(Text, nullable=False)
    showcase_type = db.Column(db.String(50), nullable=False)  # video, audio, image, document, demo
    file_url = db.Column(db.String(500))
    external_url = db.Column(db.String(500))
    funding_goal = db.Column(db.Float, default=0.0)
    current_funding = db.Column(db.Float, default=0.0)
    is_published = db.Column(db.Boolean, default=False)
    publication_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    
    # Relationships
    project = db.relationship('Project', backref='publications')
    creator = db.relationship('User', backref='publications')
    
    def funding_percentage(self):
        if self.funding_goal <= 0:
            return 0
        return min((self.current_funding / self.funding_goal) * 100, 100)
    
    def __repr__(self):
        return f'<Publication {self.title}>'
