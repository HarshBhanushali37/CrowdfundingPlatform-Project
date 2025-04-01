import logging
import os
from datetime import datetime

def send_notification_email(recipient_email, subject, message):
    """
    Mock function to send email notifications.
    In a production environment, this would use an actual email service.
    """
    logging.info(f"MOCK EMAIL to {recipient_email}")
    logging.info(f"Subject: {subject}")
    logging.info(f"Message: {message}")
    
    # In a real application, you would use a service like:
    # - Flask-Mail
    # - SendGrid API
    # - AWS SES
    # - Mailgun API
    
    # Example with Flask-Mail (commented out as not implemented in this demo)
    # from flask_mail import Message
    # from app import mail
    # msg = Message(subject, sender='noreply@foodaid.org', recipients=[recipient_email])
    # msg.body = message
    # mail.send(msg)
    
    return True

def format_currency(amount):
    """Format a number as INR currency"""
    return "₹{:,.2f}".format(amount)

def format_date(date):
    """Format a date nicely"""
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    return date.strftime('%B %d, %Y')

def get_campaign_category_icon(category):
    """Get appropriate icon for campaign category"""
    icons = {
        'emergency': 'alert-circle',
        'community': 'users',
        'children': 'child',
        'elderly': 'heart',
        'international': 'globe',
        'education': 'book-open',
        'other': 'tag'
    }
    return icons.get(category, 'tag')
