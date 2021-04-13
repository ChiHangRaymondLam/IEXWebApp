#Author: Sunil Lal

#This is a simple HTTP server which listens on port 8080, accepts connection request, and processes the client request 
#in sepearte threads. It implements basic service functions (methods) which generate HTTP response to service the HTTP requests. 
#Currently there are 3 service functions; default, welcome and getFile. The process function maps the requet URL pattern to the service function.
#When the requested resource in the URL is empty, the default function is called which currently invokes the welcome function.
#The welcome service function responds with a simple HTTP response: "Welcome to my homepage".
#The getFile service function fetches the requested html or img file and generates an HTTP response containing the file contents and appropriate headers.

#To extend this server's functionality, define your service function(s), and map it to suitable URL pattern in the process function.

#This web server runs on python v3
#Usage: execute this program, open your browser (preferably chrome) and type http://servername:8080
#e.g. if server.py and broswer are running on the same machine, then use http://localhost:8080

'''
Name: Chi Hang Lam
Student ID.: 17026690
159352
Assignment 1
11 April 2021
'''

'''
When open portfolio and stock, need to refresh the page or wait to load the getSymbol function.
After that, the select optin can work fine.
Still thinking how to solve this problem.

I also find that in Dropdown option for select the symbols.
Need to configure the limit of "json.maxitemsComputed" in VS code to display over 1x,xxx symbols
Now, I set it to 15,000.
'''

from socket import *
import _thread
import pycurl
from io import BytesIO
import sys
import pandas as pd
import numpy as np
import json
from base64 import b64encode


#Basic authorization variables
username = '17026690'
password = '17026690'
encoded_credentials = b64encode(bytes(f'{username}:{password}',
                                encoding='ascii')).decode('ascii')
#print(encoded_credentials)


#IEX APT TOKEN
IEX_API_TOKEN = 'pk_cc8fcab40a8b4d2fb5b21fcc2a05df54'


#Socket Server
serverSocket = socket(AF_INET, SOCK_STREAM)

#serverHost = '127.0.0.1'
serverPort = int(sys.argv[1])
#serverPort = 8080
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))

serverSocket.listen(5)
print('The server is running ...')	
# Server should be up and running and listening to the incoming connections


#Check Authorization
def checkForLogin():
    header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=''\r\n\r\n".encode()
    body = "You must login ... ".encode()
    return header, body


def loginInSuccess():
    header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    body = "Authenticated!".encode()
    return header, body


#Extract the given header value from the HTTP request message
def getHeader(message, header):
	if message.find(header) > -1:
		value = message.split(header)[1].split()[2] # split()[0] -> get the ":"
		#print("Value: " + value)
	else:
		value = None
	return value


#service function to fetch the requested file, and send the contents back to the client in a HTTP response.
def getFile(filename):
	try:
		#print(filename)
		f = open(filename, "rb") # rb - Open in binary mode (read/write using byte data)
		# Store the entire content of the requested file in a temporary buffer
		body = f.read()

		# if the filename ends with (png||jpg) then set the Content-Type to be "image/(png||jpg)"
		if filename.endswith(('png', 'jpg')):
			contentType = "image/" + filename.split('.')[-1]
			#print(contentType)
		# else set the Content-Type to be "text/html"
		else:
			contentType = "text/html"

		header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()

	except IOError:
		# Send HTTP response message for resource not found
		header = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
		body = "<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n".encode()

	return header, body


#service function to generate HTTP response with a simple welcome message
def welcome(message):
	contentType = "text/html"
	header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()
	f = open('index.html', "rb")
	body = f.read()

	return header, body


#default service function
def default(message):
	header, body = welcome(message)
	
	return header, body


#Update portfolio
def updateportfolio(message):
	#print(message)
	input_data = message.split()[61]
	#print(input_data)
	input_data_list = input_data.split('&')
	#print(input_data_list)

	values = []
	haveRecord = False

	for i in range(len(input_data_list)):
		values.append(input_data_list[i].split('='))
	#print(values)

	symbol = values[0][1]
	quantity = int(values[1][1])
	price = int(values[2][1])

	#Load the portfolio data from json file
	with open('portfolio.json', 'r') as f:
		datas = json.load(f)

	#Check update record in json file or not
	for i in range(len(datas)):
		if datas[i]['Stock'] == symbol:
			haveRecord = True
			old_quantity = int(datas[i]['Quantity']) 
			old_price = int(datas[i]['Price']) 
			#If quantity more than original, return
			if old_quantity + quantity < 0:
				print('You have not enough quantity.')
				
				contentType = "text/html"
				header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()
				f = open('portfolio.html', "rb")
				body = f.read()

				return header, body

			#Modify the record
			gain_or_loss = calculate_gain_or_loss(symbol, quantity, price)
			
			newquantity = old_quantity + quantity
			newprice = int((old_quantity * old_price + price * quantity) / newquantity)
			
			datas[i]['Quantity'] = newquantity
			datas[i]['Price'] = newprice
			datas[i]['GainOrLoss'] = gain_or_loss

	if haveRecord == False:
		# #Add new record
		gain_or_loss = calculate_gain_or_loss(symbol, quantity, price)

		dict1 = {'Stock': symbol , 'Quantity': quantity, 'Price': price, 'GainOrLoss': gain_or_loss}
		datas.append(dict1)

	#Save Json file
	with open('portfolio.json', 'w') as outfile:
		json.dump(datas, outfile)
			
	contentType = "text/html"
	header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()
	f = open('portfolio.html', "rb")
	body = f.read()

	return header, body


#Portfolio
def portfolio(message):
	dataList = []
	getSymbol()

	#Load the portfolio data from json file
	with open('portfolio.json', 'r') as f:
		datas = json.load(f)

	if datas != []:
		contentType = "text/html"
		header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()
		f = open('portfolio.html', "rb")
		body = f.read()

		return header, body

	contentType = "text/html"
	header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()
	f = open('portfolio.html', "rb")
	body = f.read()

	return header, body


#Stock Chart
def stock(message):
	getSymbol()
	#print(message)
	try:
		input_data = message.split()[61]
		#print(input_data)
		input_data_list = input_data.split('=')
		#print(input_data_list)
		symbol = input_data_list[1]
		#print(symbol)

		getClosePriceChart(symbol)

	except:
		print("No meesage input!")

	contentType = "text/html"
	header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()
	f = open('stock.html', "rb")
	body = f.read()

	return header, body


# Get Closing price chart
def getClosePriceChart(symbol):
	chart_buffer = BytesIO()
	curl = pycurl.Curl()

	ticker = symbol
	IEX_API_TOKEN = 'Tsk_30a2677082d54c7b8697675d84baf94b'
    
	api_chart_url = f'https://sandbox.iexapis.com/stable/stock/{ticker}/chart/ytd?chartCloseOnly=true&token={IEX_API_TOKEN}'

	#Find the close price and plot a chart
	curl.setopt(curl.SSL_VERIFYPEER, False)
	curl.setopt(curl.URL, api_chart_url)
	curl.setopt(curl.WRITEFUNCTION, chart_buffer.write)

	curl.perform()
	curl.close()

	body = chart_buffer.getvalue().decode('UTF-8')

	close_data = json.loads(body)

	date_list = []
	close_list = []

	dict1 = []

	for i in range(len(close_data)):
		date_list.append(close_data[i]['date'])
		close_list.append(close_data[i]['close'])

	data_dict = dict(zip(date_list, close_list))

	data_list = [{'date': date, 'close': close} for date, close in zip(date_list, close_list)]

	#Save date and closing price into json file
	with open('chart.json', 'w') as outfile:
		json.dump(data_list, outfile)


#Get IEX Symbol
def getSymbol():
	symbol_buffer = BytesIO()
	curl = pycurl.Curl()

	api_symbol_url = f'https://cloud.iexapis.com/stable/ref-data/symbols?token={IEX_API_TOKEN}'

	curl.setopt(curl.SSL_VERIFYPEER, False)
	curl.setopt(curl.URL, api_symbol_url)
	curl.setopt(curl.WRITEFUNCTION, symbol_buffer.write)

	curl.perform()
	curl.close()

	body = symbol_buffer.getvalue().decode('UTF-8')

	symbol_data = json.loads(body)

	symbol_list = []
	symbol_list_value = []

	for i in range(len(symbol_data)):
		symbol_list.append(i)
		symbol_list_value.append(symbol_data[i]['symbol'])

	data_dict = dict(zip(symbol_list, symbol_list_value))

	data_list = [{'symbol': symbol, 'value': value} for symbol, value in zip(symbol_list, symbol_list_value)]

	#Save the symbols to json file
	with open('symbol.json', 'w') as outfile:
 		json.dump(data_list, outfile)


#Calculate Gain or Loss
def calculate_gain_or_loss(symbol, quantity, price):
	response_buffer = BytesIO()
	curl = pycurl.Curl()

	ticker = symbol

	api_url = f'https://cloud.iexapis.com/stable/stock/{ticker}/quote?token={IEX_API_TOKEN}'

	#Set the curl options which specify the Google API server, the parameters to be passed to the API,
	# and buffer to hold the response
	curl.setopt(curl.SSL_VERIFYPEER, False)
	curl.setopt(curl.URL, api_url)
	curl.setopt(curl.WRITEFUNCTION, response_buffer.write)

	curl.perform()
	curl.close()

	#Parse the XML data received from google API, and generate HTTP response using it
	body = response_buffer.getvalue().decode('UTF-8')

	ticker_data = json.loads(body)

	#Calculate Gain or Loss
	latestPrice = ticker_data['latestPrice']
	#print(latestPrice)
	gain_or_loss = str(int((latestPrice - price)/price*100))+'%'

	return gain_or_loss


#We process client request here. The requested resource in the URL is mapped to a service function which generates the HTTP reponse 
#that is eventually returned to the client. 
def process(connectionSocket) :	
	# Receives the request message from the client
	message = connectionSocket.recv(4096).decode()
	#print(getHeader(message, 'Authorization'))

	if len(message) > 1:

		#Check Authorization
		if getHeader(message, 'Authorization') == encoded_credentials:
			# Extract the path of the requested object from the message
			# Because the extracted path of the HTTP request includes
			# a character '/', we read the path from the second character
			resource = message.split()[1][1:]
			#print(resource)
			#If the login is successful, redirect to following page
			if resource == "":
				responseHeader, responseBody = default(message)
			elif resource == "welcome":
				responseHeader,responseBody = welcome(message)
			elif resource == "portfolio":
				responseHeader, responseBody = portfolio(message)
			elif resource == "updateportfolio":
				responseHeader, responseBody = updateportfolio(message)
			elif resource == "stock":
				responseHeader, responseBody = stock(message)
			else:
				responseHeader,responseBody = getFile(resource)
		else:
			responseHeader, responseBody = checkForLogin()

		#map requested resource (contained in the URL) to specific function which generates HTTP response 

	# Send the HTTP response header line to the connection socket
	connectionSocket.send(responseHeader)
	# Send the content of the HTTP body (e.g. requested file) to the connection socket
	connectionSocket.send(responseBody)
	# Close the client connection socket
	connectionSocket.close()


#Main web server loop. It simply accepts TCP connections, and get the request processed in seperate threads.
while True:

	# Set up a new connection from the client
	connectionSocket, addr = serverSocket.accept()
	#Clients timeout after 60 seconds of inactivity and must reconnect.
	connectionSocket.settimeout(60)
	# start new thread to handle incoming request
	_thread.start_new_thread(process,(connectionSocket,))
