from flask import Flask, Blueprint, request, render_template, \
                  redirect, url_for, current_app

from google.cloud import storage
import json
import logging
import os
import re
import sqlite3
import urllib.parse

hearthsounds = Blueprint('hs', __name__, template_folder='templates',
                         static_folder='static', static_url_path='/static/hs')

current_dir = os.path.dirname(os.path.realpath(__file__))

class Card:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.type = data.get('type')
        self.collectable = data.get('collectible')
        self.rarity = data.get('rarity')
        self.URL_BASE = 'https://storage.googleapis.com/hearthsounds/'

        self.sounds = {}
        self.SOUND_TYPES = [
            'play',
            'stinger',
            'attack',
            'death',
            'trigger',
            'customsummon',
        ]

    def img(self):
        return ('https://media.services.zam.com/v1/media/byName/'
                'hs/cards/enus/{}.png'.format(self.id))

    def sound_url(self, file_name):
        return self.URL_BASE + file_name

    def search_name(self):
        """The name used when searching the sound files."""
        return self.name.replace(' ', '')

    def find_sounds(self, db):
        sql = 'select * from sounds where file_name match ?'
        terms = [self.id, self.search_name(), self.name.replace(' ', '_')]
        for term in terms:
            term = '{}*'.format(term)
            for row in db.execute(sql, (term,)):
                if self.sound_url(row[0]) not in self.sounds.values():
                    self.add_sound(row[0])

    def add_sound(self, name):
        """
        Add sound file to sounds dictionary.

        @param name: sound file to add to sounds.

        """
        for type in self.SOUND_TYPES:
            if type in name.lower():
                if type in ['customsummon', 'stinger']:
                    type = 'play'
                type = type.capitalize()
                n = 1
                while True:
                    if n == 1:
                        type_str = type
                    else:
                        type_str = '{} {}'.format(type, n)

                    if type_str not in self.sounds:
                        self.sounds[type_str] = self.sound_url(name)
                        return
                    n += 1

        current_app.logger.warning('UNMATCHED: {}'.format(name))

    def skip(self):
        if self.type not in ['MINION'] or not self.collectable:
            current_app.logger.info('Skipping: {}'.format(self.name))
            return True
        return False

    def _sound_sort(self, d):
        """Order the sounds Play > Attack > Trigger > Death."""
        alphabet = 'PATD'
        try:
            index = alphabet.index(d[0][0])
        except ValueError:
            index = len(alphabet)
        return index, d[0]

    def sounds_output(self):
        return sorted(self.sounds.items(), key=self._sound_sort)

def search_pattern(search):
    # replace special characters with '.*'
    search = re.sub('[^a-z0-9]', '.*', search, re.I)
    return re.compile(search, re.I)


def card_search(query, results, db):
    cards = []
    pattern = search_pattern(query)

    for card in results:
        if not pattern.search(card.get('name', '')):
            continue

        c = Card(card)

        if c.skip():
            continue

        c.find_sounds(db)
        cards.append(c)
    return cards


def load_cards():
    with open(os.path.join(current_dir, 'cards.json')) as f:
        return json.load(f)


def load_db():
    conn = sqlite3.connect(os.path.join(current_dir, 'hs_storage.db'))
    return conn.cursor()


@hearthsounds.route('/hearthsounds.py')
def dotpy():
    return redirect(url_for('hs.index', **request.args))


@hearthsounds.route('/hearthsounds')
def index():
    q = request.args.get('q', '')
    cards = []

    results = load_cards()
    db = load_db()

    if q:
        cards = card_search(q, results, db)
    db.close()

    return render_template('template.html', q=q, cards=cards)
