from google.cloud import storage
import pytest
import requests
import urllib
import yaml

import hearthsounds

def card_search(name):
    with open('config.yml') as f:
        conf = yaml.load(f)

    # Access Hearthstone API.
    search = urllib.parse.quote(name)
    headers = {'X-Mashape-Key': conf['MASHAPE_KEY']}
    resp = requests.get(conf['API_ENDPOINT'] + search, headers=headers)
    cards = resp.json()
    return cards


@pytest.fixture(scope='module')
def bucket():
    # Setup gcloud client.
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('hearthsounds')

    yield bucket


@pytest.mark.parametrize('name,num', [
    ('zilliax', 5),
    ('arfus', 6),
    ('leeroy', 4),
    ('Dalaran Aspirant', 4),
    # The lich king sounds have ID ICC_239 for some reason.
    ('lich king', 3),
    ('tirion', 3),
])
def test_find_sounds(bucket, name, num):
    """Verify that card search returns the correct amount of files."""
    cards = card_search(name)

    for card in cards:
        c = hearthsounds.Card(card)

        if c.skip():
            continue

        c.find_sounds(bucket)

        assert len(c.sounds) == num
