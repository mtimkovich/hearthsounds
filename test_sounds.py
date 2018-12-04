from google.cloud import storage
import json
import pytest
import requests
import urllib
from unittest.mock import patch

import hearthsounds


@patch('hearthsounds.current_app')
@pytest.mark.parametrize('name,num', [
    ('zilliax', 5),
    ('arfus', 6),
    ('leeroy', 4),
    ('Dalaran Aspirant', 4),
    # The lich king sounds have ID ICC_239 for some reason.
    ('lich king', 3),
    ('tirion', 3),
    ('al akir', 3),
    ('dr boom', 5),
])
def test_find_sounds(current_app, name, num):
    """Verify that card search returns the correct amount of files."""
    current_app.logger.info = print
    current_app.logger.warning = print

    results = hearthsounds.load_cards()
    db = hearthsounds.load_db()

    cards = hearthsounds.card_search(name, results, db)

    assert len(cards) == 1
    assert len(cards[0].sounds) == num
