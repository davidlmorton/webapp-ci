#! /usr/bin/env python
import argparse
import json
from pprint import pprint, pformat
import requests


def print_response(response):
    pad = '==========================='
    dpad = pad.replace('=', '-')
    request = response.request
    print("\n#===================================================" + pad)
    print("# %s %s %s" % (response.status_code,
                request.method, request.url))
    if request.body:
        print("#----------[ Request ]------------------------------" + dpad)
        pprint(json.loads(request.body))
    print("#----------[ Response: %s ]------------------------" %
            response.status_code + dpad)
    try:
        print("JSON: %s" % pformat(response.json()))
    except json.decoder.JSONDecodeError:
        print("Text: %s" % pformat(response.text))
        print("Headers: %s" % pformat(response.headers))


def get_color(color_name):
    color_lookup = {
        "green": "#36a64f",
        "red": "#e6364f",
        "yellow": "#efef4f",
    }
    if color_name in color_lookup:
        return color_lookup[color_name]
    else:
        return color_lookup['green']


def run(channels, icon_url, text, title, link, color, hooks_url, username):
    for channel in channels.split(','):
        body = {
            'channel': channel,
            'username': username,
            'icon_url': icon_url,
            "attachments": [
                {
                    "fallback": title + text,
                    "color": get_color(color),
                    "title": title,
                    "title_link": link,
                    "text": text,
                }
            ]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(hooks_url, data=json.dumps(body),
                headers=headers)
        print_response(response)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--channels', default='empi',
            help='Name of the channel(s) to post notification to '
                '(comma separated)')
    parser.add_argument('--hooks-url', required=True,
            help='The url for sending slack HTTP POST requests')
    parser.add_argument('--icon_url',
            default='https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcQ'
                '54WMELxKASbPBiB4qhsNW2LgvlP2JA1DB_IMY-wK83pESM-o5',
            help='A url to an image to use for the user')
    parser.add_argument('--text', required=True,
            help='Contents of message to post to slack channel')
    parser.add_argument('--title', required=True,
            help='Title of message to post to slack channel')
    parser.add_argument('--link', required=True,
            help='Link in message to post to slack channel')
    parser.add_argument('--color', default='green',
            help='Color of message to post to slack channel')
    parser.add_argument('--username', default='CI',
            help='Name of the user that shows up as having posted the message')
    return parser.parse_args()


if __name__ == '__main__':
    arguments = parse_args()
    run(**vars(arguments))
