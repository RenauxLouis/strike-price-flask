from periodic_compare_prices import compare_current_to_strike_prices
from flask import Blueprint

strikebp = Blueprint("strike", __name__)


@strikebp.cli.command("strike_price_compare")
def create():
    compare_current_to_strike_prices()
