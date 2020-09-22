#!/bin/bash
export MAIL_USERNAME = <your.email>
export MAIL_PASSWORD = <your.password>
cd /home/ubuntu/workspace/investing && /home/ubuntu/.local/bin/flask users strike_price_compare >> scheduled.log 2 > &1
