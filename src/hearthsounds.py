#!/usr/bin/env python
import cgi
import json
from mako.template import Template
import MySQLdb
import re
import requests
import yaml

print "Content-Type: text/html"
print

def verify_url(url):
    return re.match(r'(http://)?(www\.)?hearthhead\.com', url)

def get_card_id(url):
    m = re.search('/cards/([^/]*)', url)
    return m.group(1)

class Card:
    def __init__(self, card_id, db):
        self.BASE_URL = 'http://media.services.zam.com/v1/media/byName'
        self.card_id = card_id
        self.db = db
        self.cursor = db.cursor(MySQLdb.cursors.DictCursor)

    def from_json(self, j):
        self.name = j['name']
        self.image = self.BASE_URL + next(i['url'] for i in j['media'] if i['type'] == 'CARD_IMAGE')
        sound_json = [i for i in j['media'] if 'SOUND' in i['type']]
        self.sounds = self.get_sounds(sound_json)

    def from_sql(self):
        self.cursor.execute('select * from cards where card_id = %s limit 1', (self.card_id,))
        row = self.cursor.fetchone()

        if row:
            self.card_id = row['card_id']
            self.name = row['name']
            self.image = row['image']
            self.sounds = json.loads(row['sounds'])
            return True

        return False

    def get_sounds(self, sound_json):
        sounds = []
        for sound in sound_json:
            type = sound['type'].split('_')[0].title()
            url = self.BASE_URL + sound['url']
            sounds.append({'type': type, 'url': url})

        return sounds

    def insert(self):
        self.cursor.execute('insert into cards (card_id, name, image, sounds) values (%s, %s, %s, %s)',
                            (self.card_id, self.name, self.image, json.dumps(self.sounds)))
        self.db.commit()

form = cgi.FieldStorage()
url = form.getvalue('url', '')

config = yaml.load(open('/home/conf/db.yaml'))
db = MySQLdb.connect(**config)

card_name = ''
if url and verify_url(url):
    if not url.startswith('http://'):
        url = 'http://' + url

    card_id = get_card_id(url)
    card = Card(card_id, db)
    exists = card.from_sql()

    if not exists:
        r = requests.get(url)
        html = r.text.encode('utf-8')

        for line in html.splitlines():
            if 'card:' in line:
                line = line.replace('card:', '', 1)
                j = json.loads(line)
                card.from_json(j)
                card.insert()

                break

else:
    card = None

db.close()


error = ''
if url and not verify_url(url):
    error = 'Invalid url provided'

print Template(filename='template.html').render(url=cgi.escape(url, True), 
                                                card=card,
                                                error=error)
