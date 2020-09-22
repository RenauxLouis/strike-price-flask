# strike-price-flask
Flask app sending mails when strike price is reached

To setup:
- Run `python3 server_strike_price_db.py` to allow curling to the app for adding tickers with the following curl commands:
```
curl --header "Content-Type: application/json" --request GET http://<your_url>:8080/is_alive
curl --header "Content-Type: application/json" --request GET http://<your_url>:8080/read_db
curl --header "Content-Type: application/json" --request POST --data '{"ticker_to_add": "TSLA", "strike_price": 80}' http://<your_url>:8080/add_ticker
curl --header "Content-Type: application/json" --request GET http://<your_url>:8080/reset_db
```
- Edit `cron_job_template.sh` to add the email address and password to use to send emails.
- Make the `cron_job.sh`executable with
``` chmod 775 cron_job.sh ```
- Run a `cronjob -e` with the following content to run `periodic_compare_prices.py` every minute each weekday between 13h to 20h UTC (corresponding to 9h to 16h EST, verify that the instance setup uses UTC):
```
* 13-20 * * 1-5 /home/ubuntu/workspace/strike-price-flask/cron_job.sh
```
