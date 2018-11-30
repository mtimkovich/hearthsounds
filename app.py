from flask import Flask
from hearthsounds import hearthsounds

app = Flask(__name__)
app.register_blueprint(hearthsounds)
