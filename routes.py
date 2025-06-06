from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, desc
from app import db
from models import User, Circle, Project, CircleMembership, ProjectMilestone, MediaHouse, MediaHouseInvestment, AIAssistanceRequest, Pitch, Publication
from forms import LoginForm, RegisterForm, ProfileForm, CircleForm, ProjectForm, MilestoneForm
from datetime import datetime, timedelta

# Main blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Get featured circles and projects
    featured_circles = Circle.query.filter_by(is_public=True).order_by(desc(Circle.created_at)).limit(6).all()
    recent_projects = Project.query.order_by(desc(Project.created_at)).limit(6).all()
    
    return render_template('index.html', 
                         featured_circles=featured_circles,
                         recent_projects=recent_projects)

@main.route('/dashboard')
@login_required
def dashboard():
    # User's circles
    user_circles = Circle.query.filter_by(owner_id=current_user.id).all()
    joined_circles = [membership.circle for membership in current_user.circle_memberships]
    
    # User's projects
    user_projects = Project.query.filter_by(creator_id=current_user.id).all()
    
    # Recent activity (simplified for MVP)
    recent_projects = Project.query.order_by(desc(Project.created_at)).limit(5).all()
    
    return render_template('dashboard.html',
                         user_circles=user_circles,
                         joined_circles=joined_circles,
                         user_projects=user_projects,
                         recent_projects=recent_projects)

# Auth blueprint
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            full_name=form.full_name.data,
            bio=form.bio.data,
            creator_type=form.creator_type.data
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Welcome to Creovue.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

# Circles blueprint
circles = Blueprint('circles', __name__)

@circles.route('/')
def list():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Circle.query.filter_by(is_public=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(or_(
            Circle.name.contains(search),
            Circle.description.contains(search)
        ))
    
    circles_list = query.order_by(desc(Circle.created_at)).all()
    
    return render_template('circles/list.html', 
                         circles=circles_list,
                         current_category=category,
                         current_search=search)

@circles.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CircleForm()
    if form.validate_on_submit():
        circle = Circle(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            max_members=form.max_members.data,
            is_public=form.is_public.data,
            owner_id=current_user.id
        )
        db.session.add(circle)
        db.session.flush()  # To get the circle.id
        
        # Add owner as member
        membership = CircleMembership(
            user_id=current_user.id,
            circle_id=circle.id,
            role='owner'
        )
        db.session.add(membership)
        db.session.commit()
        
        flash('Circle created successfully!', 'success')
        return redirect(url_for('circles.detail', id=circle.id))
    
    return render_template('circles/create.html', form=form)

@circles.route('/<int:id>')
def detail(id):
    circle = Circle.query.get_or_404(id)
    
    # Check if user is member
    is_member = False
    user_membership = None
    if current_user.is_authenticated:
        user_membership = CircleMembership.query.filter_by(
            user_id=current_user.id, 
            circle_id=circle.id
        ).first()
        is_member = user_membership is not None
    
    # Get circle projects
    circle_projects = Project.query.filter_by(circle_id=circle.id).order_by(desc(Project.created_at)).all()
    
    return render_template('circles/detail.html', 
                         circle=circle,
                         is_member=is_member,
                         user_membership=user_membership,
                         circle_projects=circle_projects)

@circles.route('/<int:id>/join', methods=['POST'])
@login_required
def join(id):
    circle = Circle.query.get_or_404(id)
    
    # Check if already a member
    existing = CircleMembership.query.filter_by(
        user_id=current_user.id, 
        circle_id=circle.id
    ).first()
    
    if existing:
        flash('You are already a member of this circle.', 'info')
    elif circle.member_count >= circle.max_members:
        flash('This circle is full.', 'error')
    else:
        membership = CircleMembership(
            user_id=current_user.id,
            circle_id=circle.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        flash('Successfully joined the circle!', 'success')
    
    return redirect(url_for('circles.detail', id=id))

@circles.route('/<int:id>/leave', methods=['POST'])
@login_required
def leave(id):
    circle = Circle.query.get_or_404(id)
    
    membership = CircleMembership.query.filter_by(
        user_id=current_user.id, 
        circle_id=circle.id
    ).first()
    
    if not membership:
        flash('You are not a member of this circle.', 'error')
    elif membership.role == 'owner':
        flash('Circle owners cannot leave. Transfer ownership first.', 'error')
    else:
        db.session.delete(membership)
        db.session.commit()
        flash('Successfully left the circle.', 'info')
        return redirect(url_for('circles.list'))
    
    return redirect(url_for('circles.detail', id=id))

# Projects blueprint
projects = Blueprint('projects', __name__)

@projects.route('/')
def list():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Project.query
    
    if category:
        query = query.filter_by(category=category)
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(or_(
            Project.title.contains(search),
            Project.description.contains(search)
        ))
    
    projects_list = query.order_by(desc(Project.created_at)).all()
    
    return render_template('projects/list.html', 
                         projects=projects_list,
                         current_category=category,
                         current_search=search,
                         current_status=status)

@projects.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ProjectForm()
    
    # Get user's circles for selection
    user_circles = Circle.query.filter_by(owner_id=current_user.id).all()
    joined_circles = [membership.circle for membership in current_user.circle_memberships]
    all_circles = user_circles + joined_circles
    
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            creator_id=current_user.id,
            funding_goal=form.funding_goal.data or 0.0,
            funding_deadline=form.funding_deadline.data
        )
        
        # Set circle if specified
        circle_id = request.form.get('circle_id')
        if circle_id and circle_id != '':
            project.circle_id = int(circle_id)
        
        db.session.add(project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects.detail', id=project.id))
    
    return render_template('projects/create.html', form=form, circles=all_circles)

@projects.route('/<int:id>')
def detail(id):
    project = Project.query.get_or_404(id)
    
    # Get project milestones
    milestones = ProjectMilestone.query.filter_by(project_id=project.id).order_by(ProjectMilestone.order_index).all()
    
    # Check if user can edit
    can_edit = current_user.is_authenticated and (
        current_user.id == project.creator_id or
        (project.circle and current_user.id == project.circle.owner_id)
    )
    
    return render_template('projects/detail.html', 
                         project=project,
                         milestones=milestones,
                         can_edit=can_edit)

@projects.route('/<int:id>/milestone', methods=['POST'])
@login_required
def add_milestone(id):
    project = Project.query.get_or_404(id)
    
    # Check permissions
    if current_user.id != project.creator_id:
        abort(403)
    
    form = MilestoneForm()
    if form.validate_on_submit():
        milestone = ProjectMilestone(
            project_id=project.id,
            title=form.title.data,
            description=form.description.data,
            target_date=form.target_date.data,
            order_index=len(project.milestones)
        )
        db.session.add(milestone)
        db.session.commit()
        flash('Milestone added successfully!', 'success')
    
    return redirect(url_for('projects.detail', id=id))

# Profile blueprint
profile = Blueprint('profile', __name__)

@profile.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        current_user.creator_type = form.creator_type.data
        current_user.location = form.location.data
        current_user.website = form.website.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('profile/edit.html', form=form)

# Funding blueprint
funding = Blueprint('funding', __name__)

@funding.route('/dashboard')
@login_required
def dashboard():
    # Get user's projects with funding
    funded_projects = Project.query.filter_by(creator_id=current_user.id).filter(Project.funding_goal > 0).all()
    
    # Calculate stats
    total_goal = sum(p.funding_goal for p in funded_projects)
    total_raised = sum(p.current_funding for p in funded_projects)
    
    # Recent funding activity (mocked for MVP)
    recent_activity = []
    
    return render_template('funding/dashboard.html',
                         funded_projects=funded_projects,
                         total_goal=total_goal,
                         total_raised=total_raised,
                         recent_activity=recent_activity)

# Media Houses blueprint
media_houses = Blueprint('media_houses', __name__)

@media_houses.route('/')
def list():
    industry = request.args.get('industry', '')
    search = request.args.get('search', '')
    
    query = MediaHouse.query.filter_by(is_active=True)
    
    if industry:
        query = query.filter_by(industry=industry)
    
    if search:
        query = query.filter(or_(
            MediaHouse.name.contains(search),
            MediaHouse.description.contains(search)
        ))
    
    media_houses_list = query.order_by(desc(MediaHouse.created_at)).all()
    
    return render_template('media_houses/list.html', 
                         media_houses=media_houses_list,
                         current_industry=industry,
                         current_search=search)

@media_houses.route('/<int:id>')
def detail(id):
    media_house = MediaHouse.query.get_or_404(id)
    
    # Get recent investments
    recent_investments = MediaHouseInvestment.query.filter_by(
        media_house_id=media_house.id
    ).order_by(desc(MediaHouseInvestment.investment_date)).limit(5).all()
    
    return render_template('media_houses/detail.html', 
                         media_house=media_house,
                         recent_investments=recent_investments)

# AI Pilot blueprint
ai_pilot = Blueprint('ai_pilot', __name__)

@ai_pilot.route('/')
@login_required
def dashboard():
    # Get user's AI requests
    user_requests = AIAssistanceRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(AIAssistanceRequest.created_at)).limit(10).all()
    
    return render_template('ai_pilot/dashboard.html', user_requests=user_requests)

@ai_pilot.route('/request', methods=['GET', 'POST'])
@login_required
def create_request():
    if request.method == 'POST':
        request_type = request.form.get('request_type')
        description = request.form.get('description')
        project_id = request.form.get('project_id') or None
        
        ai_request = AIAssistanceRequest(
            user_id=current_user.id,
            project_id=project_id,
            request_type=request_type,
            description=description,
            status='processing'
        )
        
        # Mock AI response for demo
        ai_responses = {
            'budget_planning': 'Based on your project scope, I recommend allocating 40% to production, 25% to talent, 20% to post-production, 10% to marketing, and 5% to contingency. For a project of this scale, consider a budget range of $50,000-$80,000.',
            'script_draft': 'Here\'s a suggested outline: Act I - Character introduction and inciting incident (25%), Act II Part A - Rising action and complications (25%), Act II Part B - Midpoint and escalating conflicts (25%), Act III - Climax and resolution (25%). Focus on strong character arcs and visual storytelling.',
            'marketing_strategy': 'I suggest a three-phase approach: Pre-production (build anticipation through behind-the-scenes content), Production (document the journey), Post-production (create teasers and engage with your community). Target indie film festivals and streaming platforms.',
            'collaboration_matching': 'Based on your project category and location, I\'ve identified 12 potential collaborators in your area. Consider reaching out to cinematographers Sarah Chen and Marcus Rodriguez, who have experience in similar projects.',
            'funding_strategy': 'For optimal funding success, I recommend: 1) Create a compelling pitch deck with visual proof-of-concept, 2) Set milestone-based funding goals, 3) Engage your existing network first, 4) Apply to relevant grants and competitions, 5) Consider media house partnerships for larger projects.'
        }
        
        ai_request.ai_response = ai_responses.get(request_type, 'Thank you for your request. Our AI is analyzing your needs and will provide detailed recommendations shortly.')
        ai_request.status = 'completed'
        
        db.session.add(ai_request)
        db.session.commit()
        
        flash('AI assistance request submitted successfully!', 'success')
        return redirect(url_for('ai_pilot.dashboard'))
    
    # Get user's projects for selection
    user_projects = Project.query.filter_by(creator_id=current_user.id).all()
    
    return render_template('ai_pilot/request.html', user_projects=user_projects)

# Pitching System
pitches = Blueprint('pitches', __name__)

@pitches.route('/create/<int:project_id>')
@login_required
def create_pitch_form(project_id):
    project = Project.query.get_or_404(project_id)
    if project.creator_id != current_user.id:
        flash('You can only create pitches for your own projects.', 'error')
        return redirect(url_for('projects.detail', id=project_id))
    
    media_houses = MediaHouse.query.filter_by(is_active=True).all()
    return render_template('pitches/create.html', project=project, media_houses=media_houses)

@pitches.route('/submit', methods=['POST'])
@login_required
def submit_pitch():
    project_id = request.form.get('project_id')
    media_house_id = request.form.get('media_house_id')
    pitch_text = request.form.get('pitch_text')
    requested_amount = request.form.get('requested_amount')
    
    project = Project.query.get_or_404(project_id)
    if project.creator_id != current_user.id:
        flash('You can only create pitches for your own projects.', 'error')
        return redirect(url_for('projects.detail', id=project_id))
    
    pitch = Pitch(
        project_id=project_id,
        media_house_id=media_house_id,
        creator_id=current_user.id,
        pitch_text=pitch_text,
        requested_amount=float(requested_amount)
    )
    
    db.session.add(pitch)
    db.session.commit()
    
    flash('Pitch submitted successfully!', 'success')
    return redirect(url_for('projects.detail', id=project_id))

@pitches.route('/list')
@login_required
def list_pitches():
    user_pitches = Pitch.query.filter_by(creator_id=current_user.id).order_by(desc(Pitch.pitch_date)).all()
    return render_template('pitches/list.html', pitches=user_pitches)

@pitches.route('/media-house/<int:media_house_id>')
@login_required
def create_media_house_pitch(media_house_id):
    media_house = MediaHouse.query.get_or_404(media_house_id)
    user_projects = Project.query.filter_by(creator_id=current_user.id).all()
    
    if not user_projects:
        flash('You need to create a project before pitching to media houses.', 'warning')
        return redirect(url_for('projects.create'))
    
    return render_template('pitches/media_house_pitch.html', 
                         media_house=media_house, 
                         user_projects=user_projects)

@pitches.route('/submit-media-house', methods=['POST'])
@login_required
def submit_media_house_pitch():
    media_house_id = request.form.get('media_house_id')
    project_id = request.form.get('project_id')
    pitch_text = request.form.get('pitch_text')
    requested_amount = request.form.get('requested_amount')
    
    media_house = MediaHouse.query.get_or_404(media_house_id)
    project = Project.query.get_or_404(project_id)
    
    if project.creator_id != current_user.id:
        flash('You can only pitch your own projects.', 'error')
        return redirect(url_for('media_houses.detail', id=media_house_id))
    
    # Check if already pitched this project to this media house
    existing_pitch = Pitch.query.filter_by(
        project_id=project_id,
        media_house_id=media_house_id,
        creator_id=current_user.id
    ).first()
    
    if existing_pitch:
        flash('You have already pitched this project to this media house.', 'warning')
        return redirect(url_for('media_houses.detail', id=media_house_id))
    
    pitch = Pitch(
        project_id=project_id,
        media_house_id=media_house_id,
        creator_id=current_user.id,
        pitch_text=pitch_text,
        requested_amount=float(requested_amount),
        status='pending'
    )
    
    db.session.add(pitch)
    db.session.commit()
    
    flash(f'Your pitch for "{project.title}" has been submitted to {media_house.name}!', 'success')
    return redirect(url_for('media_houses.detail', id=media_house_id))

# AI Pilot System - Creative Assistance
ai_pilot = Blueprint('ai_pilot', __name__, url_prefix='/ai-pilot')

@ai_pilot.route('/')
@login_required
def dashboard():
    # Get user's recent AI requests
    recent_requests = AIAssistanceRequest.query.filter_by(user_id=current_user.id).order_by(desc(AIAssistanceRequest.created_at)).limit(10).all()
    
    return render_template('ai_pilot/dashboard.html', recent_requests=recent_requests)

@ai_pilot.route('/request', methods=['POST'])
@login_required
def create_request():
    request_type = request.form.get('request_type')
    description = request.form.get('description')
    project_id = request.form.get('project_id')
    
    ai_request = AIAssistanceRequest(
        user_id=current_user.id,
        project_id=project_id if project_id else None,
        request_type=request_type,
        description=description,
        status='completed'  # Instant response for now
    )
    
    # Generate instant response based on request type
    if request_type == 'budget_planning':
        ai_request.ai_response = f"""**Budget Planning Assistance for Your Project**

Based on your request: "{description}"

**Recommended Budget Breakdown:**
• Pre-production: 15-20% of total budget
• Production: 50-60% of total budget  
• Post-production: 20-25% of total budget
• Marketing & Distribution: 10-15% of total budget

**Key Cost Considerations:**
• Equipment rental or purchase
• Talent and crew compensation
• Location fees and permits
• Post-production software and services
• Marketing and promotional materials

**Budget Optimization Tips:**
• Consider equipment sharing with other creators
• Explore local talent and crew options
• Look into student or emerging professional rates
• Plan for 10-15% contingency buffer
• Research available grants and funding opportunities

Would you like more specific guidance for any particular budget category?"""
    
    elif request_type == 'script_draft':
        ai_request.ai_response = f"""**Script Development Guidance**

For your project: "{description}"

**Script Structure Framework:**
• **Act 1 (25%):** Setup, character introduction, inciting incident
• **Act 2A (25%):** Rising action, complications develop
• **Act 2B (25%):** Midpoint, stakes escalate
• **Act 3 (25%):** Climax, resolution, denouement

**Character Development Checklist:**
• Clear motivation and goals for each character
• Distinct voice and dialogue patterns
• Character arcs showing growth/change
• Backstory that informs present actions

**Scene Writing Tips:**
• Each scene should advance plot or develop character
• Start scenes late, end early
• Show don't tell wherever possible
• Use subtext in dialogue
• Create visual storytelling opportunities

**Next Steps:**
1. Complete character profiles and backstories
2. Write detailed scene-by-scene outline
3. Focus on strong opening and ending
4. Get feedback from trusted readers
5. Revise based on table reads

Need help with specific scenes or character development?"""
    
    elif request_type == 'marketing_strategy':
        ai_request.ai_response = f"""**Marketing Strategy Framework**

For your project: "{description}"

**Target Audience Analysis:**
• Define your core demographic (age, interests, platforms)
• Identify secondary audiences and crossover appeal
• Research where your audience consumes content
• Analyze successful similar projects

**Platform Strategy:**
• **Instagram/TikTok:** Behind-the-scenes content, short teasers
• **YouTube:** Longer form content, tutorials, vlogs
• **Twitter/X:** Real-time updates, community engagement
• **LinkedIn:** Professional networking, industry connections

**Content Calendar Suggestions:**
• **Pre-launch:** Behind-the-scenes, team introductions
• **Launch phase:** Teasers, countdown, exclusive previews
• **Post-launch:** Reviews, interviews, user-generated content

**Budget Allocation:**
• Organic social media: 40%
• Paid advertising: 30%
• Influencer partnerships: 20%
• PR and media outreach: 10%

**Engagement Tactics:**
• Host live Q&As and behind-the-scenes streams
• Create shareable content and challenges
• Partner with complementary creators
• Engage with industry communities and forums

Ready to dive deeper into any specific marketing channel?"""
    
    else:
        ai_request.ai_response = f"""**Creative Assistance**

Thank you for reaching out about: "{description}"

**General Creative Guidance:**
• Break down your challenge into smaller, manageable steps
• Research similar successful projects for inspiration
• Connect with other creators in your space
• Consider your unique perspective and what makes your approach different

**Resources to Explore:**
• Industry forums and communities
• Online courses and tutorials
• Networking events and workshops
• Mentorship opportunities

**Next Steps:**
1. Define your specific goals and timeline
2. Identify the key skills or knowledge you need
3. Create a step-by-step action plan
4. Set up regular check-ins to track progress

Feel free to ask more specific questions about your creative process!"""
    
    db.session.add(ai_request)
    db.session.commit()
    
    return redirect(url_for('ai_pilot.dashboard'))
