'''SQL schema for inspections database. Contains basic inspection information in "inspections" table
and, if there are any, the out of compliance items and the facility they were noted at in the 
"errors" table'''

import sqlite3

def main():
	db = sqlite3.connect('db/inspections.db')
	c = db.cursor()

	c.execute('''CREATE TABLE IF NOT EXISTS inspections (
	name TEXT,
	address TEXT,
	city TEXT,
	state TEXT,
	zipcode TEXT,
	inspection_date TEXT,
	type TEXT,
	grade TEXT
	)''')

	c.execute('''CREATE TABLE IF NOT EXISTS errors (
	inspection_name TEXT REFERENCES inspection (name), 
	address TEXT, 
	out_of_compliance TEXT
	)''')

	db.commit()
	db.close()

if __name__ == '__main__':
	main()