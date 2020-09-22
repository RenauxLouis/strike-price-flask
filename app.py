from flask import Flask
from blueprint import strikebp

app = Flask(__name__)
app.register_blueprint(strikebp)
