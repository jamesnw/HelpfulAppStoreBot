#HelpfulAppStoreBot
#adds links to apps in the App Store

import praw
import re
import sys
import json
from pprint import pprint
from time import gmtime, strftime

log_file = open('logs/log.txt','a+')

#app store info
affiliate = open(user+"private/affiliate.txt", "r").read().rstrip()
campaign = "rdtb";
aff_string = "?at=" + affiliate + "&ct=" + campaign

def comment_reply(id, name):
	"This formats a comment based on a name and id"
	string = "A link to [" + name + "](https://itunes.apple.com/app/id" + id + aff_string + ") in the iOS App Store. ([non-affiliate](https://itunes.apple.com/app/id" + id + "))\n\n"
	return string

def jlog(message):
	"Write to log with time"
	time = strftime("%d %b %Y %H:%M:%S", gmtime())
	log_file.write(time+": " + message + "\n")
	
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
## Allow for easy switching between accounts                             	
#user = "justanothertestaccou"
user = "HelpfulAppStoreBot"

username = open(user+"private/users/username.txt", "r").read().rstrip()
password = open(user+"private/users/password.txt", "r").read().rstrip()
user_agent = ("HelpfulAppStoreBot, linking to iOS Apps")

reddit = praw.Reddit(user_agent = user_agent)
reddit.login(username = username, password = password)
jlog("logged in");
    
v_fixed = []
#Look for comments
subreddit = reddit.get_subreddit('iphone+ios')
subreddit_comments = subreddit.get_comments()

already_done_file = open('logs/already_done.txt','a+')
already_done = set(line.strip() for line in open('logs/already_done.txt'))
already_done_to_add = set()

jlog("Already done: %i" % len(already_done))

#load apps
apps = json.load(open('apps.json'))

comment_posted = False

for comment in subreddit_comments:
	if comment.author != user:
		if comment.id not in already_done and comment_posted == False: 
			jlog("\t%s" % comment.id)
			reply = '';
			for app in apps:
				if app["name"] in comment.body:
					reply = reply + comment_reply(name = app["name"], id = app["id"])
					already_done.add(comment.id)
			if len(reply) > 0:
				reply = reply + "\n If you prefer to give an extra 7% to Apple instead of this bot, please use the non-affiliate link."
				print comment.body
				if query_yes_no("Post reply to this comment?"):
					posted_reply = comment.reply(reply)
					jlog("Replied to %s with %s" % (comment.id, posted_reply.id))
					comment_posted = True
					already_done_file.write(posted_reply.id+"\n");
					print "Replied"
			already_done_file.write(comment.id+"\n");
	else:
		jlog("Hey, it's you- %s" % comment.id)
