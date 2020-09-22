import os

from flask import Blueprint

from periodic_compare_prices import compare_current_to_strike_prices

strikebp = Blueprint("strike", __name__)


@strikebp.cli.command("strike_price_compare")
def create():
    sender_email = os.environ.get("MAIL_USERNAME")
    sender_password = os.environ.get("MAIL_PASSWORD")
    compare_current_to_strike_prices(sender_email, sender_password)
