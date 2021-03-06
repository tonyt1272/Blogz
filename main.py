from flask import request, redirect, render_template, session, flash #Imports for Flask server
import re
from hash_utils import check_pw_hash
from models import User, Blog
from app import app, db
from waitress import serve 		#Production server, remove this to use the hello-flask virtual

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
	allowed_routes = ['login', 'register', 'home', 'all_posts', 'display_entry','single_user_posts']
	if request.endpoint not in allowed_routes and 'email' not in session:
		if request.endpoint == 'entry':
			return redirect('/login')
		return redirect('/home')
##-------------

##Main page
@app.route("/")
def index():
	return redirect('/home')
##----------

##Home----------
@app.route('/home')
def home():

	page = request.args.get('page',1, type=int) #gets page of the paginated result to display
												#default is 1, with type set to integer
	users = User.query.paginate(page=page, per_page=25)

	return render_template('home.html', title="T-Blogz",users=users)
##--------------

##Disply all posts from a single user
@app.route("/single_user_posts")
def single_user_posts():

	user_email = request.args.get("email")
	user = User.query.filter_by(email=user_email).first()
	
	user_name = user.user_name
	title = user_name + "'s blog"

	page = request.args.get('page',1, type=int) #gets page of the paginated result to display
												#default is 1, with type set to integer
	user_posts = Blog.query.filter_by(owner=user, hidden=False).order_by(Blog.pub_date.desc()).paginate(page=page,
																										per_page=5)

	if user_email:
		if 'email' in session and user_email == session['email']:
			hidden_user_posts = Blog.query.filter_by(owner=user, hidden=True).order_by(Blog.pub_date.desc()).all()
		else:
			hidden_user_posts = None
	return render_template('/all_posts.html',title=title,user_posts=user_posts,
		hidden_user_posts=hidden_user_posts,email=user_email,user_name=user_name,single=True)
##----------

##all_posts
@app.route("/all_posts")
def all_posts():

	page = request.args.get('page',1, type=int) #gets page of the paginated result to display
												#default is 1, with type set to integer
	user_posts = Blog.query.filter_by(hidden=False).order_by(Blog.pub_date.desc()).paginate(page=page, per_page=10)

	return render_template('/all_posts.html',title="T-Blogz",user_posts=user_posts)
##----------

##Register new users
@app.route("/register", methods=['GET', 'POST'])
def register():
	if 'email' in session:
		email = session['email']
		flash('{} is currently logged in. User must logout before a new user can register.'.format(email),
			  'alert alert-warning alert-dismissible fade show')


		page = request.args.get('page', 1, type=int)  # gets page of the paginated result to display
		users = User.query.paginate(page=page, per_page=25)
		return render_template('home.html', title="T-Blogz", users=users)

	if request.method == 'POST':
		email = request.form['email']
		user_name = request.form['user_name']
		password = request.form['password']
		verify = request.form['vpassword']

		existing_user = User.query.filter_by(email=email).first()
		existing_user_name = User.query.filter_by(user_name=user_name).first()

		if existing_user:
			flash('user with email {} already exists.  Please select another user name.'.format(email),'error')
			return render_template('register.html',form_email=email,title="T-Blogz Registration",
				form_user_name=user_name)

		if existing_user_name:
			flash('user with user name {} already exists.'.format(user_name),'error')
			return render_template('register.html',form_email=email,title="T-Blogz Registration",
				form_user_name=user_name)

		if not is_email(email):
			flash('{} is not a valid email address'.format(email),'error')
			return render_template('register.html',form_email=email,title="T-Blogz Registration",
				form_user_name=user_name)

		if not user_name:
			flash('please choose a user name','error')
			return render_template('register.html',form_email=email,title="T-Blogz Registration",
				form_user_name=user_name)
			
		if password != verify:
			flash('password and verification do not match.','error')
			return render_template('register.html',form_email=email,title="T-Blogz Registration",
				form_user_name=user_name)

		if not password:
			flash('please anter and verify password.','error')
			return render_template('register.html',form_email=email,title="T-Blogz Registration",
				form_user_name=user_name)

		user = User(email=email, password=password,user_name=user_name)
		db.session.add(user)
		db.session.commit()
		session['email'] = user.email
		session['user_name'] = user.user_name
		return redirect("/entry")
	else:
		return render_template('register.html', title="T-Blogz Registration")
##-------------------

##Enter blog post
@app.route('/entry', methods = ['POST', 'GET'])
def entry():
	user = User.query.filter_by(email=session['email']).first() #match current userr in db
	title_error = None
	body_error = None
	entry_error = False
	if request.method == 'POST':
		new_title = request.form['new_title']
		new_entry = request.form['new_entry']

		if not new_title:
			entry_error = True
			title_error="Please enter a title for your post"
			
		if not new_entry:
			entry_error = True
			body_error = "Please enter your blog post in the 'New entry' form above"
			
		if entry_error:
			return render_template('blog_entry.html',title="Add a Blog Entry",
									title_error=title_error, body_error=body_error, blog_title=new_title,
									body=new_entry)

		blog = Blog(new_title, new_entry, user)
		post_body = blog.body 
		post_title = blog.title
		db.session.add(blog)
		db.session.commit()
		post_id = blog.id #the id gets assigned after the commit
		return render_template("display_entry.html",title=post_title, post_body=post_body, post_id=post_id,
								post_hidden=False, user_email=session['email'],user_name=session['user_name'])
	else:
		return render_template('blog_entry.html',title="Add a Blog Entry")
##--------------

##Display entry
@app.route('/display_entry', methods=['GET'])
def display_entry():
	pub_date = request.args.get('date_time')
	user_email = request.args.get('email')
	user = User.query.filter_by(email=user_email).first()
	user_name=user.user_name
	owner_id = user.id
	post = Blog.query.filter_by(owner_id=owner_id, pub_date=pub_date).first()
	title = post.title
	post_body = post.body
	post_id = post.id
	post_hidden = post.hidden
	return render_template("display_entry.html",title=title, post_body=post_body,
	 post_id=post_id, post_hidden=post_hidden,user_email=user_email,user_name=user_name) 
##--------------

##Existing user login
@app.route('/login', methods=['POST','GET'])
def login():
	## Delete current session before allowing another login
	if 'email' in session:
		del session['email']
		del session['user_name']
	##-----------------
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		user = User.query.filter_by(email=email).first() #.first() returns the first user object
														#If no email match, returns python None			
		if user and check_pw_hash(password, user.pw_hash):		#If user exists and user.password = password entered
			session['email'] = email 	#session object is a dictionary, here it is used to hold the
										#the user's email address
			session['user_name'] = user.user_name
			return redirect('/entry')
		else:
			flash('User password incorrect or user does not exist', 'error')

	return render_template('/login.html', title="T-Blogz Log in")
##-----------

##Hide post
@app.route('/hide', methods= ['POST'])
def hide():
	user_email = request.form['user_email']
	post_id = request.form['post_id']
	hide_post = Blog.query.get(post_id)
	hide_post.hidden = True
	db.session.add(hide_post)
	db.session.commit()
	return redirect('/single_user_posts?email={}'.format(user_email))
##-----------

##unHide post
@app.route('/unhide', methods= ['POST'])
def unhide():
	user_email = request.form['user_email']
	post_id = request.form['post_id']
	unhide_post = Blog.query.get(post_id)
	unhide_post.hidden = False
	db.session.add(unhide_post)
	db.session.commit()
	return redirect('/single_user_posts?email={}'.format(user_email))
##-----------

##Delete post
@app.route('/delete', methods= ['POST'])
def delete():
	if 'be_sure' not in request.form:  #verifying users intent to delete
		flash('Are you sure?  If you are, click delete again.','error')
		flash("If you have changed your mind just go back to the Main Blog Page.",'error')
		be_sure = True
		post_id = request.form['post_id']
		post = Blog.query.get(post_id)
		title = post.title
		post_body = post.body
		post_id = post.id
		post_hidden = post.hidden
		user_email = session['email']
		return render_template("display_entry.html",title=title, 
			post_body=post_body, post_id=post_id, post_hidden=post_hidden, be_sure = be_sure, user_email=user_email)

	post_id = request.form['post_id']
	delete_post = Blog.query.get(post_id)
	db.session.delete(delete_post)
	db.session.commit()
	return redirect('/single_user_posts?email={}'.format(session['email']))
##------------

##log out
@app.route('/logout')
def logout():
	if 'email' in session:
		del session['email']
		del session['user_name']
	return redirect('/all_posts')
##---------


@app.errorhandler(404)
def error_404(error):
	return render_template('error_pages/404.html') , 404


if __name__ == '__main__':
	app.run()				#use this with development server, only local host can access

	#serve(app, listen='*:8080')  #virtual server

	#app.run(host='0.0.0.0')	#opens the development server, this is not recommended