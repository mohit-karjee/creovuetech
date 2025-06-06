import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///creovue.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import main, auth, circles, projects, funding, profile, media_houses, ai_pilot, pitches
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(circles, url_prefix='/circles')
    app.register_blueprint(projects, url_prefix='/projects')
    app.register_blueprint(funding, url_prefix='/funding')
    app.register_blueprint(profile, url_prefix='/profile')
    app.register_blueprint(media_houses, url_prefix='/media-houses')
    app.register_blueprint(ai_pilot, url_prefix='/ai-pilot')
    app.register_blueprint(pitches, url_prefix='/pitches')

    
    with app.app_context():
        # Import models to ensure they're registered
        import models
        db.create_all()
        
        # Create default admin user if none exists
        from models import User, MediaHouse
        if not User.query.filter_by(email='admin@creovue.com').first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@creovue.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Admin User',
                bio='Platform Administrator',
                creator_type='admin'
            )
            db.session.add(admin)
            db.session.commit()
            
        # Add sample media houses
        if MediaHouse.query.count() == 0:
            media_houses_data = [
                {
                    'name': 'StreamVision Studios',
                    'description': 'Leading streaming platform focused on innovative indie content and emerging creators. We specialize in original series, documentaries, and feature films with global distribution.',
                    'industry': 'streaming',
                    'website': 'https://streamvision.com',
                    'contact_email': 'partnerships@streamvision.com',
                    'investment_range_min': 50000,
                    'investment_range_max': 2000000,
                    'preferred_categories': 'film,music,documentary,series',
                    'investment_criteria': 'We invest in original content with strong storytelling, diverse voices, and commercial potential. Looking for projects with clear target audience and distribution strategy.'
                },
                {
                    'name': 'Indie Film Collective',
                    'description': 'Boutique production house supporting independent filmmakers with funding, distribution, and mentorship programs.',
                    'industry': 'film',
                    'website': 'https://indiefilmcollective.com',
                    'contact_email': 'funding@indiefilmcollective.com',
                    'investment_range_min': 10000,
                    'investment_range_max': 500000,
                    'preferred_categories': 'film,documentary,art',
                    'investment_criteria': 'Focus on character-driven narratives, social impact themes, and emerging filmmakers with unique perspectives.'
                },
                {
                    'name': 'Digital Music Ventures',
                    'description': 'Music industry investment firm specializing in artist development, album production, and digital distribution partnerships.',
                    'industry': 'music',
                    'website': 'https://digitalmusicventures.com',
                    'contact_email': 'artists@digitalmusicventures.com',
                    'investment_range_min': 25000,
                    'investment_range_max': 1000000,
                    'preferred_categories': 'music,audio',
                    'investment_criteria': 'Seeking innovative artists with strong social media presence and potential for viral content. Priority for genre-blending and experimental music.'
                },
                {
                    'name': 'Creative Gaming Studios',
                    'description': 'Game development and publishing company investing in narrative-driven games and interactive experiences.',
                    'industry': 'gaming',
                    'website': 'https://creativegamingstudios.com',
                    'contact_email': 'publishing@creativegamingstudios.com',
                    'investment_range_min': 75000,
                    'investment_range_max': 3000000,
                    'preferred_categories': 'gaming,design,art',
                    'investment_criteria': 'Investment in indie games with innovative mechanics, strong art direction, and cross-platform potential.'
                }
            ]
            
            for house_data in media_houses_data:
                media_house = MediaHouse(**house_data)
                db.session.add(media_house)
            
            db.session.commit()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
