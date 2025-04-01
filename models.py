from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    bio = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='user', lazy='dynamic')
    donations = db.relationship('Donation', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_total_donated(self):
        return sum(d.amount for d in self.donations)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    short_description = db.Column(db.String(250))
    description = db.Column(db.Text, nullable=False)
    goal_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    location = db.Column(db.String(120))
    category = db.Column(db.String(50))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    donations = db.relationship('Donation', backref='campaign', lazy='dynamic', cascade="all, delete-orphan")
    updates = db.relationship('Update', backref='campaign', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Campaign {self.title}>'
    
    def progress(self):
        """Calculate percentage of goal reached"""
        if self.goal_amount == 0:
            return 0
        return min(int((self.current_amount / self.goal_amount) * 100), 100)
    
    def days_remaining(self):
        """Calculate days remaining until campaign ends"""
        if not self.end_date:
            return 0
        
        remaining = (self.end_date - datetime.utcnow()).days
        return max(0, remaining)
    
    def is_ended(self):
        """Check if campaign has ended"""
        if not self.end_date:
            return False
        return self.end_date < datetime.utcnow()
    
    def donor_count(self):
        """Get number of unique donors"""
        return self.donations.count()

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text)
    anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f'<Donation ${self.amount} to {self.campaign_id}>'
    
    def after_insert(self):
        """Update campaign's current amount after donation"""
        self.campaign.current_amount += self.amount
        db.session.commit()

# Register event listener for donation insertion
@db.event.listens_for(Donation, 'after_insert')
def update_campaign_amount(mapper, connection, target):
    campaign = Campaign.query.get(target.campaign_id)
    if campaign:
        campaign.current_amount += target.amount
        db.session.commit()

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def __repr__(self):
        return f'<Update {self.title} for Campaign {self.campaign_id}>'
