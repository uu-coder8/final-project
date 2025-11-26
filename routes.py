from flask import render_template, url_for, redirect, request, flash
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from PIL import Image
import os
import secrets

from app import app, basedir
from db import db
from models import User, Job
from forms import (RegistrationForm, LoginForm, AddJobForm, FilterForm, 
                   UpdateJobForm, UpdateProfileForm, UpdatePasswordForm, CompareForm)
from external_api import compare_cv_to_job


def save_profile_image(image):
    random_hex = secrets.token_hex(8)
    _, img_ext = os.path.splitext(image.filename)
    image_renamed = random_hex + img_ext

    image_path = os.path.join(basedir, 'static/images/', image_renamed)

    img = Image.open(image)
    img.thumbnail((300, 300))
    img.save(image_path)

    return image_renamed


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@app.route('/jobs', methods=['GET', 'POST'])
def home_page():
    form = FilterForm(request.args, meta={'csrf': False})
    company = request.args.get('company')
    categories = request.args.getlist('job_category')
    salary_ranges = request.args.getlist('salary_range')
    order_by = request.args.get('order_by')
    search = request.args.get('search')
    location_filter = request.args.get('location')
    page = request.args.get('page', 1, type=int)

    # base query
    query = Job.query

    # Filter by company if specified
    if company:
        query = query.filter_by(company=company)
    
    # Filter by search term
    if search:
        query = query.filter(
            (Job.title.ilike(f'%{search}%')) | 
            (Job.company.ilike(f'%{search}%')) |
            (Job.short_description.ilike(f'%{search}%')) | 
            (Job.full_description.ilike(f'%{search}%'))
        )
    
    # Filter by location
    if location_filter:
        query = query.filter(Job.location.ilike(f'%{location_filter}%'))

    # Filter by categories
    if categories:
        query = query.filter(Job.category.in_(categories))
    
    # Filter by salary ranges
    if salary_ranges:
        salary_filters = []
        for range_option in salary_ranges:
            if range_option == '1':
                salary_filters.append(Job.salary <= 50000)
            elif range_option == '2':
                salary_filters.append((Job.salary > 50000) & (Job.salary <= 100000))
            elif range_option == '3':
                salary_filters.append((Job.salary > 100000) & (Job.salary <= 150000))
            elif range_option == '4':
                salary_filters.append(Job.salary > 150000)
        
        if salary_filters:
            query = query.filter(or_(*salary_filters))
    
    # Apply ordering
    if order_by:
        if order_by == '1':  # Newest First
            query = query.order_by(Job.date_posted.desc())
        elif order_by == '2':  # Oldest First
            query = query.order_by(Job.date_posted.asc())
        elif order_by == '3':  # Highest Salary
            query = query.order_by(Job.salary.desc())
        elif order_by == '4':  # Lowest Salary
            query = query.order_by(Job.salary.asc())
    else:
        # Default ordering
        query = query.order_by(Job.date_posted.desc())

    jobs = query.paginate(page=page, per_page=10)

    return render_template('jobs.html', jobs=jobs, form=form)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/contact')
def contact_page():
    return render_template('contact.html')


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            app.logger.info(f'User {user.username} logged in')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home_page'))
        else:
            app.logger.warning(f'Failed login attempt: {form.email.data}')
            flash('Email or Password not Correct', 'danger')

    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    app.logger.info(f'User {current_user.username} logged out')
    logout_user()
    flash('Logged Out', 'success')
    return redirect(url_for('home_page'))


@app.route('/register', methods=['POST', 'GET'])
def register_page():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)

        if form.image.data:
            image_file = save_profile_image(form.image.data)
        else:
            image_file = 'default.jpg'

        user_to_create = User(firstname=form.firstname.data,
                            lastname=form.lastname.data,
                            username=form.username.data,
                            email=form.email.data,
                            password=hashed_password,
                            image_file=image_file)
        db.session.add(user_to_create)
        db.session.commit()

        login_user(user_to_create)
        app.logger.info(f'New user registered: {user_to_create.username}')
        flash("Thanks for registering! We're excited to have you.", 'success')   
        return redirect(url_for('home_page'))

    return render_template('register.html', form=form)


@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile_page():
    update_form = UpdateProfileForm()
    password_form = UpdatePasswordForm()

    jobs = Job.query.filter_by(user_id=int(current_user.id))

    if update_form.validate_on_submit() and 'submit' in request.form:
        # Handle profile picture upload
        if update_form.image.data:
            image_file = save_profile_image(update_form.image.data)
            current_user.image_file = image_file
        
        # Update user info
        current_user.firstname = update_form.firstname.data
        current_user.lastname = update_form.lastname.data
        current_user.username = update_form.username.data
        current_user.email = update_form.email.data
        
        try:
            db.session.commit()
            app.logger.info(f'Profile updated for user: {current_user.username}')
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('profile_page'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Profile update failed for {current_user.username}: {str(e)}')
            flash('Error updating profile. Please try again.', 'danger')

    elif password_form.validate_on_submit():
        # Verify current password
        if check_password_hash(current_user.password, password_form.current_password.data):
            # Update password
            hashed_password = generate_password_hash(password_form.new_password.data)
            current_user.password = hashed_password
            
            try:
                db.session.commit()
                app.logger.info(f'Password updated for user: {current_user.username}')
                flash('Your password has been updated!', 'success')
                return redirect(url_for('profile_page'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Password update failed for {current_user.username}: {str(e)}')
                flash('Error updating password. Please try again.', 'danger')
        else:
            app.logger.warning(f'Incorrect current password attempt by {current_user.username}')
            flash('Current password is incorrect!', 'danger')
    
    elif request.method == 'GET':
        update_form.firstname.data = current_user.firstname
        update_form.lastname.data = current_user.lastname
        update_form.username.data = current_user.username
        update_form.email.data = current_user.email

    return render_template('profile.html', user=current_user, jobs=jobs, 
                         update_form=update_form, password_form=password_form)


@app.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job_page():
    form = AddJobForm()

    if form.validate_on_submit():
        new_job = Job(
            title=form.title.data,
            company=form.company.data,
            location=form.location.data,
            category=form.category.data,
            salary=form.salary.data,
            short_description=form.short_description.data,
            full_description=form.full_description.data,
            date_posted=form.date_posted.data,
            date_expire=form.date_expire.data,
            user_id=current_user.id
        )

        db.session.add(new_job)
        db.session.commit()
        app.logger.info(f'Job posted: {new_job.title} by {current_user.username}')
        flash("Job posted successfully.", 'success')
        return redirect(url_for('home_page'))
    
    return render_template('addjob.html', form=form)


@app.route('/delete/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        app.logger.warning(f'Unauthorized delete attempt: User {current_user.username} tried to delete job {job_id}')
        flash('You cannot delete this job!', 'danger')
        return redirect(url_for('profile_page'))
  
    try:
        job_title = job.title
        db.session.delete(job)
        db.session.commit()
        app.logger.info(f'Job deleted: {job_title} (ID: {job_id}) by {current_user.username}')
        flash('Job deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Job deletion failed for job {job_id}: {str(e)}')
        flash('Error deleting job. Please try again.', 'danger')
    
    return redirect(url_for('profile_page'))


@app.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def update_job_page(job_id):
    job = Job.query.get_or_404(job_id)

    if job.user_id != current_user.id:
        app.logger.warning(f'Unauthorized update attempt: User {current_user.username} tried to update job {job_id}')
        flash('You do not have permission to edit this job!', 'danger')
        return redirect(url_for('profile_page'))

    form = UpdateJobForm()

    if form.validate_on_submit():
        # Update job fields
        job.title = form.title.data
        job.date_posted = form.date_posted.data
        job.date_expire = form.date_expire.data
        job.short_description = form.short_description.data
        job.full_description = form.full_description.data
        job.company = form.company.data
        job.salary = form.salary.data
        job.location = form.location.data
        job.category = form.category.data
        
        try:
            db.session.commit()
            app.logger.info(f'Job updated: {job.title} (ID: {job_id}) by {current_user.username}')
            flash('Job updated successfully!', 'success')
            return redirect(url_for('profile_page'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Job update failed for job {job_id}: {str(e)}')
            flash('Error updating job. Please try again.', 'danger')
            return redirect(url_for('update_job', job_id=job_id))
    
    elif request.method == 'GET':
        form.title.data = job.title
        form.date_posted.data = job.date_posted
        form.date_expire.data = job.date_expire
        form.short_description.data = job.short_description
        form.full_description.data = job.full_description
        form.company.data = job.company
        form.salary.data = job.salary
        form.location.data = job.location
        form.category.data = job.category

    return render_template('jobupdate.html', form=form, job=job)


@app.route('/job/<int:job_id>')
@login_required
def job_detail_page(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('jobdescription.html', job_detail=job)


@app.route('/compare/<int:job_id>', methods=['GET', 'POST'])
@login_required
def cv_compare_page(job_id):
    form = CompareForm()
    result = None
    filename = None

    job_description = Job.query.get_or_404(job_id).full_description

    if form.validate_on_submit():
        cv_file = form.cv.data

        if not cv_file:
            flash('Please select a CV file to upload.', 'warning')
            return render_template('compare.html', form=form, result=result, 
                                 filename=filename, job_id=job_id)
        
        try:
            # Save the uploaded file
            filename = secure_filename(cv_file.filename)
            filepath = os.path.join('jobboard/static/cv_folder', f"{current_user.id}_{filename}")
            cv_file.save(filepath)
            
            # Compare CV with job description
            result = compare_cv_to_job(filepath, job_description)
            
            # Clean up the file after processing
            try:
                os.remove(filepath)
            except:
                pass
            
            flash('CV comparison completed successfully!', 'success')
            
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
        
        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

    return render_template('compare.html', form=form, result=result, 
                         filename=filename, job_id=job_id)


@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_500(error):
    app.logger.error(f'Server Error: {error}')
    db.session.rollback()
    return render_template('500.html'), 500