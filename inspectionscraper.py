'''This is a proof of concept web scraper for food safety data. From a main page of inspections, it accesses
individual inspections for each facility and collects basic info on them. The program then outputs the data
to the console and in a JSON format'''

import json
import requests
import sqlite3
from collections import OrderedDict
from lxml import html

#URL of main inspection site
database = "db/inspections.db"
page_url = '''http://ca.healthinspections.us/napa/search.cfm?start=1&1=1&sd=01/01/1970&ed=
03/01/2017&kw1=&kw2=&kw3=&rel1=N.permitName&rel2=N.permitName&rel3=N.permitName&zc=&dtRng=YES&pre=similar'''

#Initializing data dictionary to be output
data = {}
data['inspections'] = []

def main():
	#Enables writing to SQL
	db = sqlite3.connect('db/inspections.db')
	c = db.cursor()

	inspection_links = []

	#Finding links to individual inspections on main site
	main_html = url_parse(page_url)[2]
	links = main_html.xpath('//a')
	for link in links:
		href = link.get('href')
		if 'Food Inspection' in href:
			inspection_links.append('http://ca.healthinspections.us' + href[2:])

	#Parsing indivdual inspection links
	for inspec in inspection_links:
		inspec_html = url_parse(inspec)[2]
		entries = inspec_html.xpath('//span[@class="blackline "]/text()')
		entries = [str(entry.strip()) for entry in entries]

		#Reading from the top section for basic info
		name = entries[0]
		address = entries[4].split('\r\n')[0]
		city = entries[4].split('\r\n')[1].split(',')[0]
		state, zipcode = entries[4].split(',')[1].split(' ')[1:3]
		inspection_date = entries[3]
		inspec_type = entries[9]

		#Reading from bottom section for grade
		grade_html = inspec_html.xpath('//table[@class="totPtsTbl"]')
		grade = inspec_html.xpath('.//td[@class="center bold"]/text()')[1].strip()

		#Reading from main table
		ooc_list = []

		inspection_table = inspec_html.xpath('//table[@class="mainTable"]')[0]
		#Pulls individual numbered inspection items
		categories = inspection_table.xpath('.//tr[td[@style="text-align: left;"]]')
		for tr in categories:
			inspection_raw = tr.xpath('.//td/text()')
			#Checks if out-of-compliance
			if inspection_raw[-1].strip().isdigit():
				ooc_list.append(inspection_raw[0])

		#Reformatting data
		inspection_data = [name, address, city, state, zipcode, inspection_date, inspec_type, grade, ooc_list]

		#Writing to data dictionary
		json_prep(inspection_data)

		#Out to Console
		write_console(inspection_data)

		#Out to SQL
		write_sql(db, inspection_data)

	#All data out to JSON
	with open('inspections.json', 'w') as outfile:  
		json.dump(data, outfile)

	db.commit()
	db.close()

#Takes a URL and outputs response, readable source, and HTML Elements list for xpathing
def url_parse(url):
	response = requests.get(url, timeout=30) #Timeout after 30s
	source = response.text
	html_list = html.fromstring(source)

	return response, source, html_list

#Takes data from an individual inspection and writes data to console
def write_console(datachunk):
	print("Facility: " + datachunk[0])
	print("Address: " + datachunk[1])
	print("City: " + datachunk[2])
	print("State: " + datachunk[3])
	print("ZIP code: " + datachunk[4])
	print("Inspection date: " + datachunk[5])
	print("Inspection type: " + datachunk[6])
	print("Inspection grade: " + datachunk[7])
	if datachunk[8]:
		print("Out of Compliance:")
		for error in datachunk[8]:
				print('\t' + error)
	else:
		print("In Compliance")
	print()

#Takes data from an individual inspection and reformats data for JSON
def json_prep(datachunk):
	data['inspections'].append({
			"Facility": datachunk[0],
			"Address": datachunk[1],
			"City": datachunk[2],
			"State": datachunk[3],
			"ZIP code": datachunk[4],
			"Inspection date": datachunk[5],
			"Inspection type": datachunk[6],
			"Inspection grade": datachunk[7],
			"Out of Compliance": datachunk[8]
		})

def write_sql(conn, datachunk):
	c = conn.cursor()
	inspection = ''' INSERT INTO inspections(name, address, city, state, zipcode, inspection_date, type, grade) 
	VALUES (?, ?, ?, ?, ?, ?, ?, ?) '''
	c.execute(inspection, datachunk[0:8])

	error = ''' INSERT INTO errors(inspection_name, address, out_of_compliance) VALUES (?, ?, ?) '''
	for entry in datachunk[8]:
		c.execute(error,(datachunk[0], datachunk[1],entry))

if __name__ == '__main__':
	main()