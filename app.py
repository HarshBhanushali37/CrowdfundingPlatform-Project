import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "foodaid_development_secret_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///foodaid.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models and create tables
with app.app_context():
    from models import User, Campaign, Donation, Update
    db.create_all()

    # Create admin user if it doesn't exist
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(email='admin@foodaid.org').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@foodaid.org',
            password_hash=generate_password_hash('adminpass'),
            is_admin=True,
            first_name='Admin',
            last_name='User'
        )
        db.session.add(admin)
        db.session.commit()

# Import forms
from forms import LoginForm, RegistrationForm, CampaignForm, DonationForm, UpdateForm, ProfileForm

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import utilities
from utils import send_notification_email

# Routes
@app.route('/')
def index():
    # Get featured campaigns (3 most recent)
    featured_campaigns = Campaign.query.filter_by(is_approved=True).order_by(Campaign.created_at.desc()).limit(3).all()
    # Get campaigns that are almost funded (>80% funded)
    almost_funded = Campaign.query.filter_by(is_approved=True).all()
    almost_funded = [c for c in almost_funded if c.progress() >= 80 and c.progress() < 100][:3]
    
    return render_template('index.html', featured_campaigns=featured_campaigns, almost_funded=almost_funded)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        from models import User
        user = User.query.filter_by(email=form.email.data).first()
        
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        
        flash('You have successfully logged in!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        from models import User
        from werkzeug.security import generate_password_hash
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))
    
    # Get user's campaigns
    user_campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
    
    # Get user's donations
    user_donations = Donation.query.filter_by(user_id=current_user.id).all()
    
    return render_template('profile.html', form=form, user_campaigns=user_campaigns, user_donations=user_donations)

@app.route('/campaigns')
def campaigns():
    page = request.args.get('page', 1, type=int)
    query = Campaign.query.filter_by(is_approved=True)
    
    # Handle filtering
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    sort = request.args.get('sort', 'recent')
    if sort == 'recent':
        query = query.order_by(Campaign.created_at.desc())
    elif sort == 'goal':
        query = query.order_by(Campaign.goal_amount.desc())
    elif sort == 'ending_soon':
        query = query.order_by(Campaign.end_date.asc())
    
    # Get paginated results
    campaigns = query.paginate(page=page, per_page=6, error_out=False)
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Campaign.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('campaigns.html', campaigns=campaigns, categories=categories, current_category=category, current_sort=sort)

@app.route('/campaign/<int:id>')
def campaign_detail(id):
    campaign = Campaign.query.get_or_404(id)
    
    # Only show approved campaigns to non-admins unless it's the owner
    if not campaign.is_approved and not current_user.is_authenticated:
        abort(404)
    if not campaign.is_approved and current_user.is_authenticated and not current_user.is_admin and campaign.user_id != current_user.id:
        abort(404)
    
    # Get recent updates
    updates = Update.query.filter_by(campaign_id=campaign.id).order_by(Update.created_at.desc()).all()
    
    # Get recent donors
    donors = Donation.query.filter_by(campaign_id=campaign.id).order_by(Donation.created_at.desc()).limit(5).all()
    
    return render_template('campaign_detail.html', campaign=campaign, updates=updates, donors=donors)

@app.route('/create-campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    form = CampaignForm()
    
    if form.validate_on_submit():
        campaign = Campaign(
            title=form.title.data,
            description=form.description.data,
            short_description=form.short_description.data,
            goal_amount=form.goal_amount.data,
            end_date=form.end_date.data,
            location=form.location.data,
            category=form.category.data,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Your campaign has been created and is pending approval.', 'success')
        return redirect(url_for('campaign_detail', id=campaign.id))
    
    return render_template('create_campaign.html', form=form)

@app.route('/campaign/<int:id>/donate', methods=['GET', 'POST'])
@login_required
def donate(id):
    campaign = Campaign.query.get_or_404(id)
    
    # Only allow donations to approved campaigns
    if not campaign.is_approved:
        flash('This campaign is not yet approved for donations.', 'warning')
        return redirect(url_for('campaign_detail', id=id))
    
    form = DonationForm()
    
    if form.validate_on_submit():
        donation = Donation(
            amount=form.amount.data,
            comment=form.comment.data,
            anonymous=form.anonymous.data,
            user_id=current_user.id,
            campaign_id=campaign.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(donation)
        db.session.commit()
        
        # Send notification email to campaign owner (mock)
        send_notification_email(
            campaign.user.email,
            f"New donation to {campaign.title}",
            f"Your campaign has received a new donation of ${donation.amount} from {'Anonymous' if donation.anonymous else current_user.username}."
        )
        
        flash('Thank you for your generous donation!', 'success')
        return redirect(url_for('campaign_detail', id=id))
    
    return render_template('donate.html', form=form, campaign=campaign)

@app.route('/campaign/<int:id>/update', methods=['GET', 'POST'])
@login_required
def add_update(id):
    campaign = Campaign.query.get_or_404(id)
    
    # Only campaign owner can add updates
    if campaign.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    form = UpdateForm()
    
    if form.validate_on_submit():
        update = Update(
            title=form.title.data,
            content=form.content.data,
            campaign_id=campaign.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(update)
        db.session.commit()
        
        flash('Your update has been posted.', 'success')
        return redirect(url_for('campaign_detail', id=id))
    
    return render_template('add_update.html', form=form, campaign=campaign)

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    
    # Get stats for dashboard
    total_campaigns = Campaign.query.count()
    pending_campaigns = Campaign.query.filter_by(is_approved=False).count()
    total_donations = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    total_users = User.query.count()
    
    # Get recent donations
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(10).all()
    
    # Get campaigns pending approval
    pending_approval = Campaign.query.filter_by(is_approved=False).all()
    
    return render_template('admin/dashboard.html', 
                           total_campaigns=total_campaigns,
                           pending_campaigns=pending_campaigns,
                           total_donations=total_donations,
                           total_users=total_users,
                           recent_donations=recent_donations,
                           pending_approval=pending_approval)

@app.route('/admin/campaigns')
@login_required
def admin_campaigns():
    if not current_user.is_admin:
        abort(403)
    
    campaigns = Campaign.query.all()
    return render_template('admin/manage_campaigns.html', campaigns=campaigns)

@app.route('/admin/campaign/<int:id>/approve', methods=['POST'])
@login_required
def approve_campaign(id):
    if not current_user.is_admin:
        abort(403)
    
    campaign = Campaign.query.get_or_404(id)
    campaign.is_approved = True
    db.session.commit()
    
    # Send notification email to campaign creator (mock)
    send_notification_email(
        campaign.user.email,
        "Campaign Approved",
        f"Your campaign '{campaign.title}' has been approved and is now live on our platform."
    )
    
    flash('Campaign has been approved.', 'success')
    return redirect(url_for('admin_campaigns'))

@app.route('/admin/campaign/<int:id>/reject', methods=['POST'])
@login_required
def reject_campaign(id):
    if not current_user.is_admin:
        abort(403)
    
    campaign = Campaign.query.get_or_404(id)
    
    # Instead of deleting, we could set a "rejected" flag, but for simplicity we'll delete
    db.session.delete(campaign)
    db.session.commit()
    
    # Send notification email to campaign creator (mock)
    send_notification_email(
        campaign.user.email,
        "Campaign Rejected",
        f"We're sorry, but your campaign '{campaign.title}' has been rejected. Please contact us for more information."
    )
    
    flash('Campaign has been rejected and removed.', 'warning')
    return redirect(url_for('admin_campaigns'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
