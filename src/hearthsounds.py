#!/usr/bin/env python
from bs4 import BeautifulSoup
import cgi
import json
from mako.template import Template
import sqlite3
import re
import requests

print "Content-Type: text/html"
print

def verify_url(url):
    return re.match(r'(http://)?(www\.)?hearthpwn\.com/cards/', url)

def get_card_id(url):
    m = re.search('/cards/([^/]*)', url)
    return m.group(1)

class Card:
    def __init__(self, card_id, db):
        self.card_id = card_id
        self.db = db
        self.cursor = db.cursor()

    def from_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        self.name = soup.find('h2').text
        self.image = soup.find('img', class_='hscard-static')['src']
        audio = soup.find_all('audio')
        self.sounds = []
        for a in audio:
            id = a['id'].replace('sound', '').replace('1', '')
            src = a['src']

            self.sounds.append({'id': id, 'src': src})

    def from_sql(self):
        self.cursor.execute('select * from cards where card_id = ? limit 1', (self.card_id,))
        row = self.cursor.fetchone()

        if row:
            self.card_id = row['card_id']
            self.name = row['name']
            self.image = row['image']
            self.sounds = json.loads(row['sounds'])
            return True

        return False

    def insert(self):
        self.cursor.execute('insert into cards (card_id, name, image, sounds) values (?, ?, ?, ?)',
                            (self.card_id, self.name, self.image, json.dumps(self.sounds)))
        self.db.commit()

form = cgi.FieldStorage()
url = form.getvalue('url', '')

db = sqlite3.connect('/home/protected/hearthsounds.db')
db.row_factory = sqlite3.Row

card_name = ''
error = ''

if url and verify_url(url):
    if not url.startswith('http://'):
        url = 'http://' + url

    card_id = get_card_id(url)
    card = Card(card_id, db)
    exists = card.from_sql()

    if not exists:
        try:
            r = requests.get(url)
            html = r.text.encode('utf-8')
            card.from_html(html)
            card.insert()
        except requests.ConnectionError:
            error = 'Error connecting to Hearthpwn'
            card = None

else:
    card = None

db.close()

if url and not verify_url(url):
    error = 'Invalid url provided'

print Template(filename='template.html').render(url=cgi.escape(url, True), 
                                                card=card,
                                                error=error)
