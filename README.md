# strike-price-flask
Flask app sending mails when strike price is reached

To setup:
- Run `server_strike_price_db.py` to allow curling to the app for adding tickers 
- Run a `cronjob -e` with the following content to run `periodic_compare_prices.py` every minute each weekday between 13h to 20h UTC (corresponding to 9h to 16h EST):
```
* 13-20 * * 1-5 /home/ubuntu/workspace/investing/cron_job.sh
```
