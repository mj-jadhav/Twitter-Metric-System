#import packages
from flask import Flask, session,jsonify, render_template, request
import flask
import tweepy


app = Flask(__name__)

#Twitter App Configuration
CONSUMER_KEY="G38cVEVzzy0qE4QKjbhig"
CONSUMER_SECRET="Df9iiJYQsx2ESuDnFA9NZuRagBLJMipi6jxOxW0gc"


@app.route("/auth")
def send_token_request():
	#Authorize the Twitter App
	global auth_url
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	try:
		# Getting the authentication	
		auth_url = auth.get_authorization_url()
		
		#Manage session of token key & secret
		session['key'] = auth.request_token.key
		session['secret'] = auth.request_token.secret
	except tweepy.TweepError:
		print 'Error! Failed to get request token'
	return flask.redirect(auth_url)

@app.route("/")
def app_init():	
	return flask.render_template('index.html')

@app.route('/share/<username>')
def influenced_by(username):
	# Manage session of influenced User
	session['influenced'] = username
	#Redirect home
	return flask.redirect("/")

@app.route("/verify")
def get_verification():
	try:
		# Retrieve the Pin
		pin = request.args.get('pin', 0, type=int)
		influenced=""
		if 'pin' in session:
			if session['pin'] == pin:#check for already exitsting pin
				#Return score stored in session
				if 'influenced' in session:
					if session['influenced'] == "":#Check value of Influenced User
						session['influenced']=''
					influenced=session['influenced']#store value of influenced_by in temporary variable
					
				#Clear the 'influenced' session
				session['influenced']="" 
				return jsonify(Username=session['username'],Followers=session['followers'],Lists=session['lists'],VerifiedCount=session['verifiedcount'],Verified=session['verified'],Contributors=session['contributors'],Blocked=session['blocked'],Protected=session['protected'],Influenced=influenced)
			 
		#Authenticate the User Pin With OAuth handler Object
		auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
		auth.set_request_token(session['key'],session['secret'])
		auth.get_access_token(pin)
	except tweepy.TweepError:
		print "Error Getting Access Token"
	#Manage session of User Pin 
	session['pin']=pin
	
	#now you have access!
	api = tweepy.API(auth)
	
	#Calculate Score of User
	calculate_score(api)
	
	#Manage session of Username
	link = "/share/"+session['username']
	if 'influenced' in session:
		if session['influenced'] == "":#Check value of Influenced User
			session['influenced']=''
		influenced=session['influenced']#store value of influenced_by in temporary variable
		#User influenced by itself
		if influenced in session['username']:
			influenced=""
	#Clear the 'influence' session
	session['influenced']=""
	
	#Return Score
	return jsonify(Username=session['username'],Followers=session['followers'],Lists=session['lists'],VerifiedCount=session['verifiedcount'],Verified=session['verified'],Contributors=session['contributors'],Blocked=session['blocked'],Protected=session['protected'],Influenced=influenced)
	
def calculate_score(api):
	
	# initialization
	followers = api.me().followers_count	# number of followers of authenticated users
	
	#Store username & Manage Session
	user_name = api.me().screen_name
	session['username']=user_name
	
	#points if followers are high
	if followers  >= 100:
		session['followers'] = 30
	else:
		session['followers'] = followers*3/10
	
	# points if user appears in a number of lists
	num_of_lists = len(api.lists_memberships())
	if num_of_lists >= 10:
		session['lists'] = 20
	else:
		session['lists'] = num_of_lists*2
	
	# points since the person has verified followers
	verifiedCount = 0;
	for follower in api.followers():
		if follower.verified==True:
			verifiedCount = verifiedCount + 1
			
	# points if verified followers >=20
	if verifiedCount >= 20:
		session['verifiedcount'] = 20
	else:
		session['verifiedcount'] = verifiedCount
		
	# points if the person is verified
	if api.me().verified == True:
		session['verified'] = 10
	else:
		session['verified'] = 0
		
	# points if contribution is enabled
	if api.me().contributors_enabled == True:
		session['contributors'] = 10
	else:
		session['contributors'] = 0
	
	# no points if the a/c has blocked quite a lot of members
	if followers/10 > len(api.blocks_ids()):
		session['blocked'] = 5
	else:
		session['blocked'] = 0
	
	# no points if the a/c is protected
	if api.me().protected == False:
		session['protected'] = 5
	else:
		session['protected'] = 0
	
	return 

	
if __name__ == "__main__":
	app.debug = True
	app.secret_key = '%\xbf\x1aW\x1f\x84\x10\x7f\xe5\x93SP;8-\x9d!\xc8\x06\x8bi\xacXG'
	app.run()

'''
****** PARAMETERS FOR CALCULATING SCORE **********
-number of followers
-number of verified followers
-account has contributors +
-account is verified +
-account is protected -
-List the lists the specified user has been added to +

'''
