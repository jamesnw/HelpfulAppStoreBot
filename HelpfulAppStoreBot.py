#!/usr/bin/python

#HelpfulAppStoreBot
#adds links to apps in the App Store

import praw
import re
import sys
import json
from pprint import pprint
from time import gmtime, strftime
import requests
import pickle
import atexit
import os
import time
import signal
from tendo import singleton
import smtplib

me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

#file-wide setup

dbFile = "logs/cachedapps.p"

#app store info
affiliate_file = open("private/affiliate.txt", "r")
affiliate = affiliate_file.read().rstrip()
affiliate_file.close()
campaign = "rdtb";
aff_string = "?at=" + affiliate + "&ct=" + campaign

appList = []

def comment_reply(id, name, subreddit):
	"This formats a comment based on a name and id"
	string = "A link to [" + name + "](https://itunes.apple.com/app/id" + id + aff_string + subreddit +") in the iOS App Store. ([non-affiliate](https://itunes.apple.com/app/id" + id + "))\n\n"
	return string

def jlog(message):
	"Write to log with time"
	time = strftime("%d %b %Y %H:%M:%S", gmtime())
	log_file = open('logs/log.txt','a+')
	log_file.write(time+": " + message + "\n")
	log_file.close()
	
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

#Create an app class
class App:
	def __init__(self, searchterm):
		self.searchterm = searchterm
		self.success = 0
		#Check if cache exists	
		global appList	
		for app in appList:
			if(self.success != 1):
				if app.searchterm == self.searchterm:
					self.success = 1
					self.id = app.id
					self.name = app.name
		if(self.success != 1):
			#no cache found, searching server
			search_url = 'https://itunes.apple.com/search'
			data = dict()
			data['term'] = searchterm
			data['media'] = 'software'
			data['limit'] = 1
			data = requests.get(url=search_url, params=data)
			if(data.status_code == 200):
				output = json.loads(data.content)
				if(output['resultCount'] > 0):
					self.id = output['results'][0]['trackId']
					self.name = output['results'][0]['trackName']
					self.success = 1
					appList.append(self)

def exit_handler():
	# Dump the caches
	global appList
	try:
		with open(dbFile, 'w+') as db_file:
			pickle.dump(appList, db_file)
	except Exception as search_exception:
		jlog(str(search_exception))
		pass
	print("Shutting Down\n")
	jlog("Shut down")
	#send email
	session = smtplib.SMTP('smtp.gmail.com', 587)
	session.ehlo()
	session.starttls()
	user_file = open("private/email-user.txt", "r")
	email = user_file.read().rstrip()
	user_file.close()
	pw_file = open("private/email-password.txt", "r")
	pw = pw_file.read().rstrip()
	pw_file.close()
	session.login(email, pw)
	headers = "\r\n".join(["from: " + email, "subject: HelpfulAppStoreBot Down!","to: " + email,"mime-version: 1.0","content-type: text/html"])
	# body_of_email can be plaintext or html!                    
	content = headers + "\r\n\r\n The bot is down."
	session.sendmail(email, email, content)
atexit.register(exit_handler)


## Allow for easy switching between accounts                             	
#user = "justanothertestaccou"
user = "HelpfulAppStoreBot"

username_file = open("private/users/"+user+"/username.txt", "r")
username = username_file.read().rstrip()
username_file.close()
password_file = open("private/users/"+user+"/password.txt", "r")
password = password_file.read().rstrip()
password_file.close()
user_agent = ("HelpfulAppStoreBot, linking to iOS Apps," + user)

reddit = praw.Reddit(user_agent = user_agent)
reddit.login(username = username, password = password)
jlog("logged in");


#Look for comments
subreddits = set()
subreddits.add('iphone')
subreddits.add('ios')
subreddits.add('apphookups')
subreddits.add('iosgaming')
#subreddits.add('test')

subreddit_list = '+'.join(subreddits)

keep_on = True
def kill_handler(sig, frame):
    global keep_on
    keep_on = False
    jlog("Prompting to turn off")
    
signal.signal(signal.SIGUSR1, kill_handler)

#main loop
while(keep_on):
	jlog("Start loop")
	try:
		subreddit = reddit.get_subreddit(subreddit_list)
		subreddit_comments = subreddit.get_comments()

		already_done_file = open('logs/already_done.txt','a+')
		already_done = set(line.strip() for line in open('logs/already_done.txt'))
		already_done_to_add = set()

		#load apps
		if os.path.isfile(dbFile):
			with open(dbFile, "r+") as fi:
				if fi.tell() != os.fstat(fi.fileno()).st_size:
					appList = pickle.load(fi)

		comment_posted = False
		findAppLink = re.compile("\\bapp[\s]*link[\s]*:[\s]*(.*)", re.M)


		for comment in subreddit_comments:
			if comment.author != user:
				if comment.id not in already_done and comment_posted == False: 
					jlog("\t%s" % comment.id)
					reply = '';
			
					normalMatches = findAppLink.findall(comment.body.lower())
					if len(normalMatches) > 0:
						for match in normalMatches:
							apps = match.split(",")
							for appstring in apps:
								app = App(appstring)
								if(app.success):
									reply = reply + comment_reply(name = app.name, id = str(app.id), subreddit = comment.subreddit)
									already_done.add(comment.id)
					if len(reply) > 0:
						try:
							reply = reply + "\n [What is this?](http://www.reddit.com/r/iphone/comments/21s2yf/im_up_and_running_use_the_command_app_link/) - [Source](https://github.com/jamesnw/HelpfulAppStoreBot/)."
							posted_reply = comment.reply(reply)
							jlog("Replied to %s with %s" % (comment.id, posted_reply.id))
							comment_posted = True
							already_done_file.write(posted_reply.id+"\n");
						except praw.errors.RateLimitExceeded as rl_error:
							jlog("Doing too much, sleeping for " + str(rl_error.sleep_time))
							time.sleep(rl_error.sleep_time)
						except Exception as reply_exception:
							jlog("Exception occurred while replying: " + str(reply_exception))
							time.sleep(3)
					already_done_file.write(comment.id+"\n");
			else:
				jlog("Hey, it's you- %s" % comment.id)
		already_done_file.close()
		time.sleep(30)
	except Exception as reply_exception:
		jlog("Exception occurred in main loop: " + str(reply_exception))
		time.sleep(3)
