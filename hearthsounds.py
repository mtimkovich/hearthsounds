from flask import Flask, Blueprint, request, render_template, \
                  redirect, url_for, current_app

from google.cloud import storage
import os
import re
import requests
import urllib.parse

hearthsounds = Blueprint('hs', __name__, template_folder='templates',
                         static_folder='static', static_url_path='/static/hs')


class Card:
    def __init__(self, data):
        self.id = data.get('cardId')
        self.name = data.get('name')
        self.img = data.get('img')
        self.type = data.get('type')
        self.collectable = data.get('collectible')

        self.sounds = {}
        self.SOUND_TYPES = [
            'play',
            'attack',
            'death',
            'trigger',
            'customsummon'
        ]

    def search_name(self):
        """The name used when searching the sound files."""
        return self.name.replace(' ', '')

    def find_sounds(self, bucket):
        prefixes = [self.search_name(), 'VO_{}_'.format(self.id), self.id]
        for prefix in prefixes:
            for blob in bucket.list_blobs(prefix=prefix):
                self.add_sound(blob)

    def add_sound(self, blob):
        match = False
        for type in self.SOUND_TYPES:
            if type in blob.name.lower():
                if type == 'customsummon':
                    type = 'play'
                type = type.capitalize()
                n = 1
                while True:
                    if n == 1:
                        type_str = type
                    else:
                        type_str = '{} {}'.format(type, n)

                    if type_str not in self.sounds:
                        self.sounds[type_str] = blob.public_url
                        match = True
                        break
                    n += 1
        if not match:
            current_app.logger.warning('UNMATCHED: {}'.format(blob.name))

    def skip(self):
        if self.type not in ['Minion'] or not self.collectable:
            current_app.logger.info('Skipping: {}'.format(self.name))
            return True
        return False

    def _sound_sort(self, d):
        """Order the sounds Play > Attack > Trigger > Death and then numbers."""
        alphabet = 'PATD'
        try:
            index = alphabet.index(d[0][0])
        except ValueError:
            index = len(alphabet)
        return index, d[0]

    def sounds_output(self):
        return sorted(self.sounds.items(), key=self._sound_sort)


@hearthsounds.route('/hearthsounds.py')
def dotpy():
    return redirect(url_for('hs.index', **request.args))

@hearthsounds.route('/hearthsounds')
def index():
    q = request.args.get('q', '')
    cards = []

    # Access Hearthstone API.
    search = urllib.parse.quote(q)
    headers = {'X-Mashape-Key': current_app.config['HS_MASHAPE_KEY']}
    resp = requests.get(current_app.config['HS_API_ENDPOINT'] + search,
                        headers=headers)
    if resp.status_code != 200:
        return render_template('template.html', q=q, cards=cards)
    results = resp.json()

    # Setup gcloud client.
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(current_app.config['HS_BUCKET'])

    if q:
        for card in results:
            c = Card(card)

            if c.skip():
                continue

            c.find_sounds(bucket)
            cards.append(c)

    return render_template('template.html', q=q, cards=cards)
