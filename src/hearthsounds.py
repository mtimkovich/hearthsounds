#!/usr/bin/env python
import cgi
import json
from mako.template import Template
import peewee as pw
import re
import requests

print "Content-Type: text/html"
print

def verify_url(url):
    return re.match(r'(http://)?(www\.)?hearthhead\.com', url)

form = cgi.FieldStorage()
url = form.getvalue('url', '')

class Card:
    def __init__(self, j):
        self.BASE_URL = 'http://media.services.zam.com/v1/media/byName'
        self.name = j['name']
        self.image = self.BASE_URL + next(i['url'] for i in j['media'] if i['type'] == 'CARD_IMAGE')
        sound_json = [i for i in j['media'] if 'SOUND' in i['type']]
        self.sounds = self.get_sounds(sound_json)

    def get_sounds(self, sound_json):
        sounds = []
        for sound in sound_json:
            type = sound['type'].split('_')[0].title()
            url = self.BASE_URL + sound['url']
            sounds.append({'type': type, 'url': url})

        return sounds

db = pw.MySQLDatabase('hearthstone', user='finley')

class CardModel(pw.Model):
    url = pw.CharField(unique=True)
    name = pw.CharField()
    image = pw.CharField()
    sounds = pw.TextField()

    class Meta:
        database = db

card_name = ''
if url and verify_url(url):
    if not url.startswith('http://'):
        url = 'http://' + url

    db.connect()

    try:
        model = CardModel.get(CardModel.url == url)
    except pw.DoesNotExist:
        model = None

    if not model:
        r = requests.get(url)
        html = r.text.encode('utf-8')

        for line in html.splitlines():
            if 'card:' in line:
                line = line.replace('card:', '', 1)
                j = json.loads(line)
                card = Card(j)

                model = CardModel(url=url,
                                  name=card.name,
                                  image=card.image, 
                                  sounds=json.dumps(card.sounds))

                model.save()
                break
        db.close()
else:
    card = None


error = ''
if url and not verify_url(url):
    error = 'Invalid url provided'

print Template(filename='template.html').render(url=cgi.escape(url, True), 
                                card=model,
                                sounds=json.loads(model.sounds),
                                error=error)
