
# -*- coding: utf-8 -*-

"""
LINE Pay API SDK for Python use example
Request -> Confirm -> Refund
"""

import logging
import uuid
import os
from os.path import join, dirname
#from dotenv import load_dotenv
from flask import Flask, request, abort, render_template
from linepay import LinePayApi
from flask import render_template

# dotenv
# logger
logger = logging.getLogger("linepay")
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
logger.addHandler(sh)
formatter = logging.Formatter('%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
sh.setFormatter(formatter)

# Flask 
app = Flask(__name__)

# LINE Pay API
LINE_PAY_CHANNEL_ID = "1653839411"
LINE_PAY_CHANNEL_SECRET = "06da2a5ff63c556f2483fd91e1526bbc"
LINE_PAY_REQEST_BASE_URL = "https://{}".format(
	# set your server host name (ex. ngrok forwarding host) at HOST_NAME on .env file
	os.environ.get("localhost")
)
api = LinePayApi(LINE_PAY_CHANNEL_ID, LINE_PAY_CHANNEL_SECRET, is_sandbox=True)

# Cache
CACHE = {}

@app.route("/rt")
def index():
	return render_template('confirm.html')

@app.route("/request", methods=['GET'])
def pay_request():
	order_id = str(uuid.uuid4())
	amount = 1
	currency = "TWD"
	CACHE["order_id"] = order_id
	CACHE["amount"] = amount
	CACHE["currency"] = currency
	request_options = {
		"amount": amount,
		"currency": currency,
		"orderId": order_id,
		"packages": [
			{
				"id": "package-999",
				"amount": 1,
				"name": "Sample package",
				"products": [
					{
						"id": "product-001",
						"name": "Sample product",
						"imageUrl": "https://placehold.jp/99ccff/003366/150x150.png?text=Sample%20product",
						"quantity": 1,
						"price": 1
					}
				]
			}
		],
		"redirectUrls": {
			"confirmUrl": "http://127.0.0.1/confirm",
			"cancelUrl": LINE_PAY_REQEST_BASE_URL + "/cancel"
		}
	}
	logger.debug(request_options)
	response = api.request(request_options)
	logger.debug(response)
	# Check Payment Satus
	transaction_id = int(response.get("info", {}).get("transactionId", 0))
	check_result = api.check_payment_status(transaction_id)
	logger.debug(check_result)
	response["transaction_id"] = transaction_id
	response["paymentStatusCheckReturnCode"] = check_result.get("returnCode", None)
	response["paymentStatusCheckReturnMessage"] = check_result.get("returnMessage", None)
	return render_template("request.html", result=response)


@app.route("/confirm", methods=['GET'])
def pay_confirm():
	transaction_id = int(request.args.get('transactionId'))
	logger.debug("transaction_id: %s", str(transaction_id))
	CACHE["transaction_id"] = transaction_id
	response = api.confirm(
		transaction_id,  
		float(CACHE.get("amount", 0)), 
		CACHE.get("currency", "TWD")
	)
	logger.debug(response)
	# Check Payment Satus
	check_result = api.check_payment_status(transaction_id)
	logger.debug(check_result)
	response["transaction_id"] = transaction_id
	response["paymentStatusCheckReturnCode"] = check_result.get("returnCode", None)
	response["paymentStatusCheckReturnMessage"] = check_result.get("returnMessage", None)
	# Payment Detail
	payment_details = api.payment_details(transaction_id=transaction_id)
	logger.debug(payment_details)
	response["payment_details"] = payment_details
	return render_template("confirm.html", result=response)


@app.route("/refund", methods=['GET'])
def pay_refund():
	transaction_id = int(CACHE.get("transaction_id", 0))
	logger.debug("transaction_id: %s", str(transaction_id))
	response = api.refund(transaction_id)
	logger.debug(response)
	return response

if __name__ == "__main__":
	app.run(debug=True, port=80)