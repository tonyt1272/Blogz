from app import db,app
from datetime import datetime
from hash_utils import make_pw_hash
from flask_migrate import Migrate

Migrate(app,db)
""" This connects the application to the database in order to add on migration capabilities such as adding
    columns to the database.  To enable the line above do the following in console.:
                                   1) cd to the package directory, in this case
                                    C:\...\Blogz
                                   2) type: set FLASK_APP=models.py in console
                                   3) type: flask db init in console
                                   4) type: flask db migrate -m "created * table" in console (your notes for what was created)
                                   5) type: flask db upgrade in console to execute the update
The steps above create a migrations folder in the project which allows for the migration command.  The last two steps
will create empty tables in accordance with the classes described in the model below.
To make changes to the database tables, change the the models below, then do the steps above to update the db."""
#


class Blog(db.Model):   # Creating persistent class that represents blog posts within the application
						# This class inherits db.Model class which was imported above.  The .Model part
						# is a class imported from SQLAlchemy(), it is an inherited class.

	id = db.Column(db.Integer, primary_key=True)	#set to auto create primary keys for the data entry
	title = db.Column(db.String(120))				#creating a column holds a string 120 max length
	body = db.Column(db.String(5000))				#create the blog text attribute
	owner_id = db.Column(db.Integer, db.ForeignKey('user.id')) #links to a primary key 'user.id'
													#Creating owner id column that is integer type
													#and its value will be the the 'user.id'
													#associated with the owner passed to Task, "many to one..."
	pub_date = db.Column(db.DateTime)
	hidden = db.Column(db.Boolean)

	def __init__(self,title,body,owner):			#constructor that creates an instance
		self.title = title  						#set the input title to the title value of the object				
		self.body = body							#set the body of the object to the entered string
		self.owner = owner							#owner is a user object for the blog post
		pub_date = datetime.utcnow()
		self.pub_date = pub_date
		self.hidden = False


class User(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	user_name = db.Column(db.String(120), unique=True)
	email = db.Column(db.String(120), unique=True)  #unique=True, Not possible to add two
													#different recotds with the same email
	pw_hash = db.Column(db.String(120))
	blogs = db.relationship('Blog', backref='owner')#This is NOT a column, it is a relationship
													#that populates tasks list with task objects from the Task 
													#table such that the owner property is equal to this
													#specific user object, "one to many..."

	profile_image = db.Column(db.String(64),nullable=False,
							default='default_profile.png')

	def __init__(self, email, password,user_name):
		self.email = email
		self.pw_hash= make_pw_hash(password)
		self.user_name = user_name
##-----------------------------------------------------------------------------------------
