# -*- coding: utf-8 -*-

import configparser
import time
import traceback
import urllib
import webbrowser
import praw
import prawcore
import requests
from ini_file_validator import validate_ini_file
from distutils.util import strtobool

RETRIES = 10

user_agent = "desktop:spam.posts.remover:v1.0.2 (by /u/MrBloodyshadow)"


def load_config():
    section_hunter = 'hunter', ['client_id', 'client_secret', 'username', 'password']
    section_config = 'config', ['user_to_search', 'user_to_pm', 'posts_to_search', 'delete_posts']

    valid = validate_ini_file('praw.ini', [section_hunter, section_config])
    if valid:
        global user_to_search, user_to_pm, posts_to_search, delete_posts, user_agent
        config_parser = configparser.ConfigParser()
        config_parser.read('praw.ini')

        config = config_parser['config']

        user_to_search = config['user_to_search']
        user_to_pm = config['user_to_pm']
        posts_to_search = int(config['posts_to_search'])
        delete_posts = strtobool(config['delete_posts'])

    return valid


def is_username_available(username):
    endpoint = 'https://www.reddit.com/api/username_available.json?user='
    url = endpoint + username
    response = requests.get(url)
    return response.content == 'True'


def trim_username_from_title(title):
    import re
    str_to_replace = 'Overview for '
    start_with = re.match(str_to_replace, title, re.I)
    if not start_with:
        return

    str_replaced = ''
    pattern = re.compile(str_to_replace, re.IGNORECASE)
    username = pattern.sub(str_replaced, title)
    return username


def get_user_status(username):
    try:
        redditor = reddit.redditor(username)
        if getattr(redditor, 'is_suspended', False):
            return 'suspended'  # account is suspended
    except prawcore.NotFound:
        if is_username_available(username):
            return 'not_exists'  # account doesn't exist
        else:
            return 'banned'  # account is deleted or shadowbanned for spam
    else:
        return 'exists'  # account exists


def get_spam_posts(username, sub_to_search='spam', limit=100):
    subreddit = reddit.subreddit(sub_to_search)
    submissions = subreddit.search('Overview for author:' + username, sort='relevance', limit=limit, syntax='lucene')

    active = []
    banned = []
    for submission in submissions:

        title = submission.title

        username = trim_username_from_title(title)
        if not username:
            continue
        result = r_c(get_user_status, username)
        time.sleep(2)
        print('Spam post found for user: ' + username)
        id = submission.id

        data = id, username

        if result == 'banned':
            banned.append(data)
        else:
            active.append(data)
    return banned, active


def to_url(text, url):
    return '[' + text + '](' + url + ')'


def create_report(spam_posts):
    banned_users = '|Banned users: \n-\n|'
    if not spam_posts[0].__len__() == 0:
        for banned in spam_posts[0]:
            banned_users += to_url(banned[1], '/r/spam/' + banned[0]) + ', '
        banned_users = banned_users[:-2] + '.'
    else:
        banned_users += 'None.'

    separation = '\n___\n'
    active_users = '|Active users: \n-\n|'

    if not spam_posts[1].__len__() == 0:
        for active in spam_posts[1]:
            active_users += to_url(active[1], '/r/spam/' + active[0]) + ', '
        active_users = active_users[:-2] + '.'

    else:
        active_users += 'None.'

    msg = banned_users + separation + active_users
    return msg


# Retries a connection up to RETRIES time.
def r_c(func, *args, **kwargs):
    from requests.packages.urllib3.exceptions import ProtocolError
    from requests.exceptions import ConnectionError
    from prawcore.exceptions import RequestException
    count = 0
    while count < RETRIES:
        count += 1
        try:
            return func(*args, **kwargs)
        # Timeouts and server failures
        except (ProtocolError, ConnectionError, RequestException, urllib.error.URLError):
            time.sleep(2)


try:
    print("Program started.")
    if load_config():
        print("Configuration loaded.")
        reddit = r_c(praw.Reddit, 'hunter', user_agent=user_agent)
        me = r_c(reddit.user.me)
        print("Logged in.")
        spam_posts = r_c(get_spam_posts, user_to_search, limit=posts_to_search)
        msg = create_report(spam_posts)
        redditor = r_c(reddit.redditor, user_to_pm)
        report_title = 'Spam report'
        sent = r_c(redditor.message, report_title, msg)
        print("Report sent!")
        for message in reddit.inbox.messages(limit=5):
            b1 = message.subject == report_title
            b2 = not message.new
            if b1 and b2:
                url = 'www.reddit.com/message/messages/' + message.id
                webbrowser.open(url)
                break

        if delete_posts:
            print("Deleting posts...")
            for banned in spam_posts[0]:
                submission = reddit.submission(id=banned[0])
                submission.delete()
except prawcore.exceptions.OAuthException as ex:
    print('Error from praw: ' + str(ex))
except Exception as ex:
    tb = traceback.format_exc()
    print(tb)

print('Done.')
