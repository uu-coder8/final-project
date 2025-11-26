import unittest
import os
import tempfile
from app import app
from db import db, init_db
from models import User, Job
from werkzeug.security import generate_password_hash
from datetime import date, timedelta


class FlaskTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and database before each test"""
        # Create a temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test users
            user1 = User(
                firstname='John',
                lastname='Doe',
                username='johndoe',
                email='john@test.com',
                password=generate_password_hash('password123'),
                image_file='default.jpg',
                registration_date=date.today()
            )
            
            user2 = User(
                firstname='Jane',
                lastname='Smith',
                username='janesmith',
                email='jane@test.com',
                password=generate_password_hash('password456'),
                image_file='default.jpg',
                registration_date=date.today()
            )
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Create test jobs
            job1 = Job(
                title='Python Developer',
                company='Tech Corp',
                location='New York',
                category='IT',
                salary=80000,
                short_description='Looking for Python developer',
                full_description='We need an experienced Python developer...',
                date_posted=date.today(),
                date_expire=date.today() + timedelta(days=30),
                user_id=user1.id
            )
            
            job2 = Job(
                title='Data Scientist',
                company='Data Inc',
                location='San Francisco',
                category='IT',
                salary=120000,
                short_description='Data scientist needed',
                full_description='Looking for experienced data scientist...',
                date_posted=date.today(),
                date_expire=date.today() + timedelta(days=30),
                user_id=user2.id
            )
            
            db.session.add(job1)
            db.session.add(job2)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    # ========== ROUTE TESTS ==========
    
    def test_home_page(self):
        """Test home page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_jobs_page(self):
        """Test jobs page loads successfully"""
        response = self.client.get('/jobs')
        self.assertEqual(response.status_code, 200)
    
    def test_about_page(self):
        """Test about page loads successfully"""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
    
    def test_contact_page(self):
        """Test contact page loads successfully"""
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page_get(self):
        """Test login page loads successfully"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page_get(self):
        """Test register page loads successfully"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    # ========== LOGIN TESTS ==========
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email or Password not Correct', response.data)
    
    def test_login_wrong_email(self):
        """Test login with non-existent email"""
        response = self.client.post('/login', data={
            'email': 'nonexistent@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email or Password not Correct', response.data)
    
    def test_logout(self):
        """Test logout functionality"""
        # Login first
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Then logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged Out', response.data)
    
    def test_login_redirect_if_authenticated(self):
        """Test that logged-in users are redirected from login page"""
        # Login first
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Try to access login page again
        response = self.client.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    # ========== REGISTRATION TESTS ==========
    
    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post('/register', data={
            'firstname': 'New',
            'lastname': 'User',
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Check if user was created by trying to find them in database
        with app.app_context():
            user = User.query.filter_by(email='newuser@test.com').first()
            self.assertIsNotNone(user)
    
    # ========== PERMISSION TESTS - ADD JOB ==========
    
    def test_add_job_requires_login(self):
        """Test that adding a job requires login"""
        response = self.client.get('/add_job', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to login page
    
    def test_add_job_success(self):
        """Test successful job posting"""
        # Login first
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Add a job with data that meets all validation requirements
        response = self.client.post('/add_job', data={
            'title': 'New Job Title Here',
            'company': 'Test Company',
            'location': 'Test City',
            'category': 'IT',
            'salary': 70000,
            'short_description': 'This is a short description that is long enough to meet requirements',
            'full_description': 'This is a full description that is definitely long enough to meet the minimum 50 character requirement for this field',
            'date_posted': date.today().strftime('%Y-%m-%d'),
            'date_expire': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Verify job was created in database
        with app.app_context():
            job = Job.query.filter_by(title='New Job Title Here').first()
            self.assertIsNotNone(job)
    
    # ========== PERMISSION TESTS - DELETE JOB ==========
    
    def test_delete_own_job_success(self):
        """Test user can delete their own job"""
        # Login as user1 (john@test.com)
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Get the job ID for user1's job
        with app.app_context():
            job = Job.query.filter_by(title='Python Developer').first()
            job_id = job.id
        
        # Delete the job
        response = self.client.post(f'/delete/{job_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Job deleted successfully', response.data)
    
    def test_delete_other_user_job_forbidden(self):
        """Test user cannot delete another user's job"""
        # Login as user1 (john@test.com)
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Try to delete user2's job
        with app.app_context():
            job = Job.query.filter_by(title='Data Scientist').first()
            job_id = job.id
        
        # Attempt to delete
        response = self.client.post(f'/delete/{job_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You cannot delete this job', response.data)
    
    def test_delete_job_requires_login(self):
        """Test that deleting a job requires login"""
        with app.app_context():
            job = Job.query.first()
            job_id = job.id
        
        response = self.client.post(f'/delete/{job_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to login page
    
    # ========== PERMISSION TESTS - UPDATE JOB ==========
    
    def test_update_own_job_success(self):
        """Test user can update their own job"""
        # Login as user1
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Get the job ID
        with app.app_context():
            job = Job.query.filter_by(title='Python Developer').first()
            job_id = job.id
        
        # Update the job with data that meets validation requirements
        response = self.client.post(f'/update_job/{job_id}', data={
            'title': 'Senior Python Developer',
            'company': 'Tech Corp',
            'location': 'New York',
            'category': 'IT',
            'salary': 90000,
            'short_description': 'This is an updated description that meets the minimum length requirements',
            'full_description': 'This is an updated full description that definitely meets the minimum 50 character requirement',
            'date_posted': date.today().strftime('%Y-%m-%d'),
            'date_expire': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Verify job was updated in database
        with app.app_context():
            updated_job = Job.query.get(job_id)
            self.assertEqual(updated_job.title, 'Senior Python Developer')
            self.assertEqual(updated_job.salary, 90000)
    
    def test_update_other_user_job_forbidden(self):
        """Test user cannot update another user's job"""
        # Login as user1
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        # Try to update user2's job
        with app.app_context():
            job = Job.query.filter_by(title='Data Scientist').first()
            job_id = job.id
        
        response = self.client.get(f'/update_job/{job_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You do not have permission', response.data)
    
    def test_update_job_requires_login(self):
        """Test that updating a job requires login"""
        with app.app_context():
            job = Job.query.first()
            job_id = job.id
        
        response = self.client.get(f'/update_job/{job_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to login page
    
    # ========== PROFILE TESTS ==========
    
    def test_profile_requires_login(self):
        """Test that profile page requires login"""
        response = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to login page
    
    def test_profile_page_access(self):
        """Test logged-in user can access profile"""
        # Login first
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
    
    # ========== JOB DETAIL TESTS ==========
    
    def test_job_detail_requires_login(self):
        """Test that job detail page requires login"""
        with app.app_context():
            job = Job.query.first()
            job_id = job.id
        
        response = self.client.get(f'/job/{job_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to login page
    
    def test_job_detail_page_access(self):
        """Test logged-in user can access job details"""
        # Login first
        self.client.post('/login', data={
            'email': 'john@test.com',
            'password': 'password123'
        })
        
        with app.app_context():
            job = Job.query.first()
            job_id = job.id
        
        response = self.client.get(f'/job/{job_id}')
        self.assertEqual(response.status_code, 200)
    
    # ========== SEARCH AND FILTER TESTS ==========
    
    def test_search_jobs(self):
        """Test job search functionality"""
        response = self.client.get('/jobs?search=Python')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Python', response.data)
    
    def test_filter_by_location(self):
        """Test filtering jobs by location"""
        response = self.client.get('/jobs?location=New York')
        self.assertEqual(response.status_code, 200)
    
    def test_filter_by_category(self):
        """Test filtering jobs by category"""
        response = self.client.get('/jobs?job_category=IT')
        self.assertEqual(response.status_code, 200)
    
    def test_order_by_salary(self):
        """Test ordering jobs by salary"""
        response = self.client.get('/jobs?order_by=3')  # Highest salary
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()