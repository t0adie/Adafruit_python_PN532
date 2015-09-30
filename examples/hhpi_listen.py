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

import RPi.GPIO as GPIO

import sqlite3
import MySQLdb

from datetime import time
from datetime import datetime
from datetime import timedelta
from time import sleep

import Adafruit_PN532 as PN532

import hhpi_courses
from hhpi_registration import register

# Calculate the total time the rider has been on course
t = datetime.now() - timedelta(hours=9)
s = t.strftime("%H:%M:%S")

# GPIO configuration for buzzer and button
BUTTON = 17
BUZZER = 27

# PN532 configuration for a Raspberry Pi:
CS   = 18
MOSI = 23
MISO = 24
SCLK = 25

# Configure the key to use for writing to the MiFare card.  You probably don't
# need to change this from the default below unless you know your card has a
# different key associated with it.
CARD_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# Number of seconds to delay after building a block.  Good for slowing down the
# update rate to prevent flooding new blocks into the world.
MAX_UPDATE_SEC = 1

# Create and initialize an instance of the PN532 class.
pn532 = PN532.PN532(cs=CS, sclk=SCLK, mosi=MOSI, miso=MISO)
pn532.begin()
pn532.SAM_configuration()

class read_tag:

    def __init__(self):

	print 'HHHH Rider Tag Listener'
	print ''
	print 'Waiting for HHHH Rider wristband...'
	while True:
	    # Wait for a card to be available.
	    uid = pn532.read_passive_target()
	    # Try again if no card found.
	    if uid is None:
	        continue
	    # Found a card, now try to read block 4 to detect the block type.
	    print 'Found card with UID 0x{0}'.format(binascii.hexlify(uid))
	    # Authenticate and read block 4.
	    if not pn532.mifare_classic_authenticate_block(uid, 4, PN532.MIFARE_CMD_AUTH_B, 
	                                                   CARD_KEY):
	        print 'Failed to authenticate with card!'
	        continue
	    data = pn532.mifare_classic_read_block(4)
	    if data is None:
	        print 'Failed to read data from card!'
	        continue
	    # Check if card has Hilly Hundred information by looking for header 'HHHH'
	    if data[0:4] != 'HHHH':
	        print 'This tag has not been registered as a Hilly Hundred 2015 rider!'
	        continue
            # Make the RPi beep to indicate a card has been detected
            GPIO.output(BUZZER,True)
            time.sleep(0.1)
            GPIO.output(BUZZER,False)
	    
	    # Parse out the rider's bib number and course selection.
	    bib_id = data[4]
	    course_id = data[5]
	    # Find the course number (it's ugly to search for it, but there are less than 100).
	    for course in hhpi_courses.COURSES:
	        if course[1] == course_id:
	            course_name = course[0]
	            break
	    print 'Found the information!'
	    print 'Bib No: {0}'.format(bib_id)
	    print 'Course: {0}'.format(course_name)
	    print 'Ride Time: ' + s
	    
	    # Write to the database
	    # Connect to the database
 	    db = sqlite3.connect('/var/www/ride_info.db')
 	    # Set the cursor
	    c = db.cursor()
	    # Insert the information into the table
	    c.execute('INSERT INTO hhpi_checkpoint (bib_id, course_id, cp_id, cp_timestamp) values (?, ?, ?, ?)', (bib_id, course_id, 1, s))
	    # Save (commit) the changes
	    db.commit()
	    # Close the connection
	    db.close()
	    
	    cnx = MySQLdb.connect("208.66.2.18", "t0ad13", "T0ad!nthehole", "hhPi_results")
	    cursor = cnx.cursor()
	    
	    add_rider = ("INSERT INTO checkpoint "
            "(bib_id, cp_id, cp_tin) "
            "VALUES (%s, %s, %s)")
            
            data_rider = (bib_id, 1, s)
            
            # Insert the rider's information
            cursor.execute(add_rider, data_rider)
            
            # Commit the data to the database
            cnx.commit()
            
            cursor.close()
            cnx.close() 
	    
	    print ''
	    print ''
	    print 'Press BUTTON to read tag...'
	    
	    # Break out of the reading loop and instigate another
	    break

def main():

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUZZER, GPIO.OUT)

    print ''
    print ''
    print 'Press BUTTON to read tag...'
    
    while True:
        input_state = GPIO.input(BUTTON)
        if input_state == False:
            read_tag()

if __name__ == "__main__":
    main()    
