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


def get_card_id(url):
    m = re.search('/cards/([^/]*)', url)
    return m.group(1)


def search_hearthpwn(query, db):
    c = db.cursor()
    c.execute('select card_id from searches where query = ?', (query,))
    cards = c.fetchall()
    c.close()

    if cards:
        results = [r['card_id'] for r in cards]

        return (results, True)

    r = requests.get('http://www.hearthpwn.com/cards/minion',
                     params={'filter-name': query, 'filter-premium': 1})
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find('tbody').find_all('tr')

    if cards[0].find('td', class_='no-results'):
        return ([], True)

    results = []
    for card in cards:
        details = card.find('td', class_='visual-details-cell')
        card_url = details.find('h3').find('a')['href']
        card_id = get_card_id(card_url)
        results.append(card_id)

    return (results, False)


def get_card(card_id, db):
    card = Card(card_id, db)
    exists = card.from_sql()

    if not exists:
        r = requests.get('http://www.hearthpwn.com/cards/' + card_id)
        html = r.text.encode('utf-8')
        card.from_html(html)
        card.insert()

    return card


class Card:
    def __init__(self, card_id, db):
        self.card_id = card_id
        self.db = db

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
        self.c = self.db.cursor()
        self.c.execute('select * from cards where card_id = ? limit 1', (self.card_id,))
        row = self.c.fetchone()

        if row:
            self.card_id = row['card_id']
            self.name = row['name']
            self.image = row['image']
            self.sounds = json.loads(row['sounds'])
            self.c.close()
            return True

        self.c.close()
        return False

    def insert(self):
        self.c = self.db.cursor()
        self.c.execute('insert into cards (card_id, name, image, sounds) values (?, ?, ?, ?)',
                       (self.card_id, self.name, self.image, json.dumps(self.sounds)))
        self.db.commit()
        self.c.close()


def connect(db_file):
    db = sqlite3.connect(db_file)
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('pragma foreign_keys = ON')
    c.close()

    return db


form = cgi.FieldStorage()
q = form.getvalue('q', '')

db = connect('/home/protected/hearthsounds.db')

card_name = ''
error = ''
cards = []

if q:
    q = q.lower().strip()
    results, in_cache = search_hearthpwn(q, db)

    c = db.cursor()
    for card_id in results:
        cards.append(get_card(card_id, db))

        if results and not in_cache:
            c.execute('insert into searches (query, card_id) values (?, ?)', (q, card_id))
            db.commit()
    c.close()


db.close()

print Template(filename='template.html').render(q=cgi.escape(q, True),
                                                cards=cards)
