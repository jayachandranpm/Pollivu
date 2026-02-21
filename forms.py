"""
Pollivu - WTForms Definitions
All form classes for authentication, API key management,
AI generation, poll creation, editing, and voting.
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, BooleanField, 
                     PasswordField, HiddenField)
from wtforms.validators import (DataRequired, Length, Email, EqualTo, 
                                 Optional, ValidationError)
import re


# ============================================================================
# Password Validation
# ============================================================================
def strong_password(form, field):
    """Validate password strength."""
    password = field.data
    
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number.')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).')


# ============================================================================
# Authentication Forms
# ============================================================================
class RegistrationForm(FlaskForm):
    """User registration form with strong password validation."""
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=255, message='Email must not exceed 255 characters.')
    ])
    
    display_name = StringField('Display Name (Optional)', validators=[
        Optional(),
        Length(max=100, message='Display name must not exceed 100 characters.')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        strong_password
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])


class LoginForm(FlaskForm):
    """User login form."""
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    
    remember_me = BooleanField('Remember me')


class UpdateAccountForm(FlaskForm):
    """User account update form."""
    
    display_name = StringField('Display Name', validators=[
        Length(max=100, message='Display name must not exceed 100 characters.')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=255)
    ])
    
    current_password = PasswordField('Current Password (Required to save changes)', validators=[
        DataRequired(message='Please enter your current password to save changes.')
    ])
    
    new_password = PasswordField('New Password (Optional)', validators=[
        Optional(),
        strong_password
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match.')
    ])


# ============================================================================
# API Key Forms
# ============================================================================
class APIKeyForm(FlaskForm):
    """Form for managing AI provider API keys."""
    
    gemini_key = StringField('Google Gemini API Key', validators=[
        Optional(),
        Length(max=255)
    ])
    gemini_model = StringField('Gemini Model', validators=[
        Optional(),
        Length(max=100)
    ])
    
    openai_key = StringField('OpenAI API Key', validators=[
        Optional(),
        Length(min=20, max=255, message='OpenAI API key must be at least 20 characters.')
    ])
    openai_model = StringField('OpenAI Model', validators=[
        Optional(),
        Length(max=100)
    ])
    
    claude_key = StringField('Anthropic Claude API Key', validators=[
        Optional(),
        Length(max=255)
    ])
    claude_model = StringField('Claude Model', validators=[
        Optional(),
        Length(max=100)
    ])
    



# ============================================================================
# AI Generation Forms
# ============================================================================
class AIGenerateForm(FlaskForm):
    """Form for AI-powered poll generation."""
    
    topic = StringField('Topic or Description', validators=[
        DataRequired(message='Please enter a topic for your poll.'),
        Length(min=5, max=500, message='Topic must be between 5 and 500 characters.')
    ])
    
    provider = SelectField('AI Provider', choices=[
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI (GPT-4)'),
        ('claude', 'Anthropic Claude')
    ], validators=[DataRequired()])
    
    num_options = SelectField('Number of Options', choices=[
        ('3', '3 options'),
        ('4', '4 options'),
        ('5', '5 options'),
        ('6', '6 options'),
    ], default='4')
    
    style = SelectField('Poll Style', choices=[
        ('neutral', 'Neutral & Balanced'),
        ('fun', 'Fun & Casual'),
        ('professional', 'Professional'),
        ('educational', 'Educational')
    ], default='neutral')


class AISuggestForm(FlaskForm):
    """Form for AI suggestions on existing polls."""
    
    question = TextAreaField('Current Question', validators=[
        DataRequired(),
        Length(max=500)
    ])
    
    options = TextAreaField('Current Options (one per line)', validators=[
        DataRequired()
    ])
    
    provider = SelectField('AI Provider', choices=[
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI (GPT-4)'),
        ('claude', 'Anthropic Claude')
    ], validators=[DataRequired()])


# ============================================================================
# Poll Forms
# ============================================================================
class PollOptionForm(FlaskForm):
    """Sub-form for a single poll option."""
    class Meta:
        csrf = False
    
    option_text = StringField('Option', validators=[
        DataRequired(message='Option cannot be empty.'),
        Length(min=1, max=200, message='Option must be between 1 and 200 characters.')
    ])


class PollCreationForm(FlaskForm):
    """Form for creating a new poll."""
    
    question = TextAreaField('Question', validators=[
        DataRequired(message='Please enter a question.'),
        Length(min=10, max=500, message='Question must be between 10 and 500 characters.')
    ])
    
    option_1 = StringField('Option 1', validators=[
        DataRequired(message='At least 2 options are required.'),
        Length(min=1, max=200, message='Option must be between 1 and 200 characters.')
    ])
    
    option_2 = StringField('Option 2', validators=[
        DataRequired(message='At least 2 options are required.'),
        Length(min=1, max=200, message='Option must be between 1 and 200 characters.')
    ])
    
    option_3 = StringField('Option 3', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_4 = StringField('Option 4', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_5 = StringField('Option 5', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_6 = StringField('Option 6', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_7 = StringField('Option 7', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_8 = StringField('Option 8', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_9 = StringField('Option 9', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    option_10 = StringField('Option 10', validators=[
        Optional(),
        Length(max=200, message='Option must not exceed 200 characters.')
    ])
    
    expiration = SelectField('Poll Expiration', choices=[
        ('never', 'Never'),
        ('1h', '1 Hour'),
        ('24h', '24 Hours'),
        ('7d', '7 Days'),
        ('30d', '30 Days')
    ], default='7d')
    
    allow_vote_change = BooleanField('Allow voters to change their vote')
    
    show_results_before_voting = BooleanField('Show results before voting')
    
    is_public = BooleanField('Make poll publicly accessible', default=True)
    
    def get_options(self):
        """Get all non-empty options as a list."""
        options = []
        for i in range(1, 11):
            option = getattr(self, f'option_{i}').data
            if option and option.strip():
                options.append(option.strip())
        return options
    
    def validate(self, extra_validators=None):
        """Custom validation for the form."""
        if not super().validate(extra_validators):
            return False
        
        options = self.get_options()
        
        if len(options) < 2:
            self.option_1.errors.append('At least 2 options are required.')
            return False
        
        # Check for duplicate options
        unique_options = set(opt.lower() for opt in options)
        if len(unique_options) != len(options):
            self.option_1.errors.append('All options must be unique.')
            return False
        
        return True


class EditPollForm(FlaskForm):
    """Form for editing existing poll settings."""
    
    question = TextAreaField('Question', validators=[
        DataRequired(message='Please enter a question.'),
        Length(min=10, max=500, message='Question must be between 10 and 500 characters.')
    ])
    
    expiration = SelectField('Poll Expiration', choices=[
        ('never', 'Never'),
        ('1h', '1 Hour'),
        ('24h', '24 Hours'),
        ('7d', '7 Days'),
        ('30d', '30 Days')
    ])
    
    allow_vote_change = BooleanField('Allow voters to change their vote')
    
    show_results_before_voting = BooleanField('Show results before voting')
    
    is_public = BooleanField('Make poll publicly accessible')
    
    share_results_chart = BooleanField('Share results chart publicly')
    
    share_results_list = BooleanField('Share results list publicly')
    
    share_insights = BooleanField('Share insights publicly')


class VoteForm(FlaskForm):
    """Form for submitting a vote."""
    
    option = HiddenField('Selected Option', validators=[
        DataRequired(message='Please select an option.')
    ])
