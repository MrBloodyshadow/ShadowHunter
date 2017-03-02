# -*- coding: utf-8 -*-
import json
import praw
import prawcore
import codecs
import requests
import urllib

reddit = praw.Reddit('hunter')
reddit.user.me()

user_to_search = 'Borax'
user_to_pm = 'Borax'


def is_username_available(username):
    endpoint = 'https://www.reddit.com/api/username_available.json?user='
    url = endpoint + username
    response = requests.get(url)
    return response.content == 'True'


def get_user_status(username):
    try:
        if getattr(reddit.redditor(username), 'is_suspended', False):
            return 'suspended'  # account is suspended
    except prawcore.NotFound:
        if is_username_available(username):
            return 'not_exists'  # account doesn't exist
        else:
            return 'banned'  # account is deleted or shadowbanned for spam
    else:
        return 'exists'  # account exists


def get_submissions(username, limit=0, before='', sort='new'):
    if not before.startswith('t3_'):
        before = ''
    endpoint = 'https://www.reddit.com/user/{}/submitted.json?sort={}&limit={}&before={}'
    url = endpoint.format(username, sort, limit, before)
    print(url)
    request = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'pls let me test the api'
        }
    )
    response = urllib.request.urlopen(request)
    # response = requests.get(url)
    return response


def get_spam_user(title):
    import re
    str_to_replace = 'Overview for '
    start_with = re.match(str_to_replace, title, re.I)
    if not start_with:
        return

    str_replaced = ''
    pattern = re.compile(str_to_replace, re.IGNORECASE)
    username = pattern.sub(str_replaced, title)
    return username


def get_spam_posts(username, sub_to_search='spam', limit=10):
    response = get_submissions(username, limit=limit)
    reader = codecs.getreader("utf-8")
    json_dic = json.load(reader(response))
    childrens = json_dic['data']['children']

    active = []
    banned = []
    for children in childrens:
        subreddit = children['data']['subreddit']

        if subreddit == sub_to_search:
            title = children['data']['title']

            username = get_spam_user(title)
            if not username:
                continue
            result = get_user_status(username)

            id = children['data']['id']

            data = []
            data.append(id)
            data.append(username)
            if result == 'banned':
                # submission = reddit.submission(id=id)
                # submission.delete()
                active.append(data)
            else:
                banned.append(data)
    return banned, active


def to_url(text, url):
    return '[' + text + '](' + url + ')'


tuples = get_spam_posts(user_to_search)

banned_users = '|Banned users: \n-\n|'
for banned in tuples[0]:
    banned_users += to_url(banned[1], '/r/spam/' + banned[0]) + ', '
banned_users = banned_users[:-2]

separation = '\n___\n'

active_users = '|Active users: \n-\n|'
for active in tuples[1]:
    active_users += to_url(active[1], '/r/spam/' + active[0]) + ', '
active_users = active_users[:-2]

msg = banned_users + separation + active_users

reddit.redditor(user_to_pm).message('Spam report', msg)

print('Done.')
