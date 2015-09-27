# Raspberry Pi Hilly Hundred NFC Tag Registration
# Author: Derek Naulls
# Copyright (c) 4D Concepts
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import binascii
import sys

import sqlite3

import Adafruit_PN532 as PN532

import hhpi_courses
from hhpi_registration import register

#PN532 configuration for a Raspberry Pi:
CS   = 18
MOSI = 23
MISO = 24
SCLK = 25

# Configure the key to use for writing to the MiFare card.  You probably don't
# need to change this from the default below unless you know your card has a
# different key associated with it.
CARD_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# Create and initialize an instance of the PN532 class.
pn532 = PN532.PN532(cs=CS, sclk=SCLK, mosi=MOSI, miso=MISO)
pn532.begin()
pn532.SAM_configuration()

class new_tag:

    def __init__(self):

	print "====================================================================="
	print "            Welcome to the Hilly Hundred Registration Form           "
	print "====================================================================="
	print ""
	print "This program is intended to write a rider's bib number  course"
	print "to their tag. Please note: Lost or misplaced tags must be reported"
	print "imediatly so that a new tag can be created. Also, there will be a"
	print "$25.00 replacement charg for any tag that is not recovered before the"
	print "end of tour."
	print ""
	print ""
	print "------------Step 1------------"
	print ""
	reg = register()
	fname = raw_input("What is your first name? ")
	lname = raw_input("What is your last name? ")
	bib_id = raw_input("What is your bib number? ")
	
	
	course_distance = None
	while course_distance is None:
	    print ""
	    print "------------Step 2------------"
	    print ""
	    print "Type either L to list course names, or type the course number."
	    print ""
	    choice = raw_input('Enter choice (L or block #): ')
	    print ""
	    if choice.lower() == "l":
	        # Print course names and numbers
	        print "Course Title\t\tNumber"
	        print "----------------------\t------"
	        for i, d in enumerate(hhpi_courses.COURSES):
	            course_name, course_id = d
	            print "{0:>6}\t{1}".format(course_name, i)
	    else:
	        # Assume a course has been entered.
	        try:
	            course_distance = int(choice)
	        except ValueError:
	            # Something other than a number was entered. Try again.
	            print "Error! Unrecognized option."
	            continue
	        #Check choice is within bounds of course numbers.
	        if not(0 <= course_distance < len(hhpi_courses.COURSES)):
	            print "Error! Your option seems to be out of bounds."
	            continue
	
	course_name, course_id = hhpi_courses.COURSES[course_distance]
	print ""
	print 'Place the card to be written on the PN532...'
	uid = pn532.read_passive_target()
	while uid is None:
	    uid = pn532.read_passive_target()
	print ''
	print '=============================================================='
	print 'WARNING: DO NOT REMOVE CARD FROM WRITER UNTIL FINISHED!'
	print '=============================================================='
	print ''
	# Confirm writing the bib number and course duration.    
	print ""
	print "------------Step 3------------"
	print ""
	print "You bib number is "+ bib_id + " and you are riding the {0}".format(course_name)
	print "Is this information correct?"
	choice = raw_input('Confirm card write (Y or N)? ')
	if choice.lower() != 'y' and choice.lower() != 'yes':
	    print 'Aborted!'
	    print ""
	    sys.exit(0)
	print ""
	print "Writing card (DO NOT REMOVE CARD FROM PN532)..."
	print ""
	print ""
	
	# Write to the database
	# Connect to the database
	db = sqlite3.connect('/var/www/ride_info.db')
	# Set the cursor
	c = db.cursor()
	# Insert the information into the table
	c.execute('INSERT INTO hhpi_rider (firstname, lastname, bib_id, course_id) values (?, ?, ?, ?)', (fname, lname, bib_id, course_id))
	# Save (commit) the changes
	db.commit()
	# Close the connection
	db.close()

	# Write the card!
	# First authenticate block 4.
	if not pn532.mifare_classic_authenticate_block(uid, 4, PN532.MIFARE_CMD_AUTH_B, 
	                                               CARD_KEY):
	    print 'Error! Failed to authenticate block 4 with the card.'
	    sys.exit(-1)
	# Next build the data to write to the card.
	# Format is as follows:
	# - Bytes 0-3 are a header with ASCII value 'HHHH'
	# - Byte 4 is the bib ID byte
	# - Byte 5 is the course ID byte
	data = bytearray(16)
	data[0:4] = 'HHHH'  # Header 'HHHH'
	data[4]   = int(bib_id) & 0xFF
	data[5]   = course_id & 0XFF
	# Finally write the card.
	if not pn532.mifare_classic_write_block(4, data):
	    print 'Error! Failed to write to the card.'
	    sys.exit(-1)
	print 'Wrote card successfully! You may now remove the card from the PN532.'
	
    
def main():

    while True:
	
	new_tag()

if __name__ == "__main__":
    main()
