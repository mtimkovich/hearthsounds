from flask import Flask, Blueprint, request, render_template, redirect, url_for

from bs4 import BeautifulSoup
import re
import requests
from requests import RequestException

hearthsounds = Blueprint('hs', __name__, template_folder='templates',
                         static_folder='static', static_url_path='/static/hs')


class Card:
    def __init__(self, card_id):
        self.card_id = card_id
        r = requests.get('http://www.hearthpwn.com/cards/' + self.card_id)
        html = r.text

        soup = BeautifulSoup(html, 'html.parser')
        self.name = soup.find('h2').text
        self.image = soup.find('img', class_='hscard-static')['src']
        audio = soup.find_all('audio')
        self.sounds = []
        for a in audio:
            id = a['id'].replace('sound', '').replace('1', '')
            src = a['src']

            self.sounds.append({'id': id, 'src': src})


def search_hearthpwn(query):
    r = requests.get('http://www.hearthpwn.com/cards/minion',
                     params={'filter-name': query, 'filter-premium': 1})

    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find('tbody').find_all('tr')

    if cards[0].find('td', class_='no-results'):
        return []

    results = []
    for card in cards:
        details = card.find('td', class_='visual-details-cell')
        card_url = details.find('h3').find('a')['href']
        card_id = re.search('/cards/([^/]*)', card_url).group(1)
        results.append(card_id)

    return results


@hearthsounds.route('/hearthsounds.py')
def dotpy():
    return redirect(url_for('hs.index', **request.args))

@hearthsounds.route('/hearthsounds')
def index():
    q = request.args.get('q', '')

    cards = []

    if q:
        q = q.strip()
        try:
            results = search_hearthpwn(q)

            for card_id in results:
                cards.append(Card(card_id))
        except RequestException:
            return 'hearthpwn appears to be down'

    return render_template('template.html', q=q, cards=cards)
