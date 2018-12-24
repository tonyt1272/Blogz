from flask import Flask, request, redirect, render_template, session, flash #Imports for Flask server
from datetime import datetime
import re

from flask_sqlalchemy import SQLAlchemy #Importing necessary sqlalchemy tools for using
										#the SQL database, the SQLAlchemy class is imported
										#from the flask_sqlalchemy module.

app = Flask(__name__)
app.config['DEBUG'] = True

##Configures the application to connect to the database
##  									typedb	drive		username:password	server	port	dbname		
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:MyNewPass@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)	#The constructor function recievs the app object and creates a 
						#database object
app.secret_key= 'test123'

class Blog(db.Model):   # Creating persistent class that represents blog posts within the application
						# This class inherits db.Model class which was created above.  The .Model part
						# is a method generated by the SQLAlchemy() constructor

	id = db.Column(db.Integer, primary_key=True)	#set to auto create primary keys for the data entry
	title = db.Column(db.String(120))				#creating a column holds a string 120 max length
	body = db.Column(db.String(5000))				#create the blog text attribute
	owner_id = db.Column(db.Integer, db.ForeignKey('user.id')) #links to a primary key 'user.id'
													#Creating owner id column that is integer type
													#and its value will be the the 'user.id'
													#associated with the owner passed to Task				
	pub_date = db.Column(db.DateTime)

	def __init__(self,title,body,owner):			#constructor that creates an instance
		self.title = title  						#set the input title to the title value of the object				
		self.body = body							#set the body of the object to the entered string
		self.owner = owner							#owner is a user object for the blog post
		pub_date = datetime.utcnow()
		self.pub_date = pub_date

class User(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True)  #unique=True, Not possible to add two
													#different recotds with the same email
	password = db.Column(db.String(120))
	blogs = db.relationship('Blog', backref='owner')#This is NOT a column, it is a relationship
													#that populates tasks list with task objects from the Task 
													#table such that the owner property is equal to this
													#specific user object.
													# 
	def __init__(self, email, password):
		self.email = email
		self.password = password
##-----------------------------------------------------------------------------------------

## user email validation
def is_email(string):#Regular expression for email validation
	pattern = re.compile(r'^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$')
	valid_email = pattern.findall(string)
	if valid_email:
		return True
	else:
		return False
##-------------

##login wall
@app.before_request	#special decorator tells flask to run this function before any request
def require_login():
	allowed_routes = ['login', 'register']
	print(session)
	if request.endpoint not in allowed_routes and 'email' not in session:
		return redirect('/login')
##-------------

##Main page
@app.route("/")
def index():
	encoded_error = request.args.get("error")
	user = User.query.filter_by(email=session['email']).first()
	user_posts = Blog.query.filter_by(owner=user).order_by(Blog.pub_date.desc()).all()
	return render_template('/index.html',title="Build a Blog",user_posts=user_posts)
##----------

##Register new users
@app.route("/register", methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		verify = request.form['vpassword']

		if not is_email(email):
			flash('{} is not a valid email address'.format(email),'error')
			return redirect('/register')

		if password != verify:
			flash('password and verification do not match.','error')
			
			return render_template('register.html',form_email=email,title="Build a Blog Registration")
        
		existing_user = User.query.filter_by(email=email).first()
		if existing_user:
			flash('user with email {} already exists.'.format(email),'error')
			return redirect('/register')
        
		user = User(email=email, password=password)
		db.session.add(user)
		db.session.commit()
		session['email'] = user.email
		flash("Logged in")
		return redirect("/")
	else:
		return render_template('register.html', title="Build a Blog Registration")
##-------------------

##Enter blog posts
@app.route('/entry', methods = ['POST', 'GET'])
def entry():
	user = User.query.filter_by(email=session['email']).first() #match current viewer in db
	title_error=None
	body_error=None
	entry_error=False
	if request.method == 'POST':
		new_title = request.form['new_title']
		new_entry = request.form['new_entry']

		if not new_title:
			entry_error = True
			title_error="Please enter a title for your post"
			
		if not new_entry:
			entry_error = True
			body_error="Please enter your blog post in the 'New entry' form above"
			
		if entry_error == True:
			return render_template('blog_entry.html',title="Add a Blog Entry",
				title_error=title_error, body_error=body_error, blog_title=new_title, body=new_entry)

		blog = Blog(new_title, new_entry, user)
		post_body = blog.body 
		post_title = blog.title
		db.session.add(blog)
		db.session.commit()
		return render_template("display_entry.html",title=post_title, post_body=post_body) 
		#return redirect('/')
	else:
		return render_template('blog_entry.html',title="Add a Blog Entry")
##--------------

##Display entry
@app.route('/display_entry', methods = ['GET'])
def display_entry():
	pub_date = request.args.get('date_time')
	user = User.query.filter_by(email=session['email']).first()
	owner_id = user.id
	post = Blog.query.filter_by(owner_id=owner_id, pub_date=pub_date).first()
	title = post.title
	post_body = post.body
	return render_template("display_entry.html",title=title, post_body=post_body) 


##--------------

##Existing user login
@app.route('/login', methods = ['POST','GET'])
def login():
	## Delete current session before allowing another login
	if 'email' in session:
		del session['email']
	##-----------------
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		user = User.query.filter_by(email=email).first() #.first() returns the first user object
														#If no email match, returns python None			
		if user and user.password == password:		#If user exists and user.password = password entered
			session['email'] = email #session object is a dictionary, here it is used to hold the
									 #the user's email address
			#flash("Logged in")
			return redirect('/')
		else:
			flash('User password incorrect or user does not exist', 'error')

	return render_template('login.html', title="Build a Blog Log in")
##----------

##log out
@app.route('/logout')
def logout():
	# if 'user' in session:
	# 	del session['user']
	if 'email' in session:
		del session['email']
	
	return redirect('/')
##---------

if __name__ == '__main__':
	app.run()