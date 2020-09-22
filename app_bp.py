from flask import Blueprint, Flask
from periodic_compare_prices import compare_current_to_strike_prices


app = Flask(__name__)
strikebp = Blueprint("strike", __name__)


@strikebp.cli.command("strike_price_compare")
def create():
    compare_current_to_strike_prices()


app.register_blueprint(strikebp)
