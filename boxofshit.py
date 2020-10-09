#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Box of Shit is a bot that monitors bathroom habits to enlighten and entertain.

BoS is built in Python and designed to run on a Raspberry Pi Zero W. The full
wiring diagram can be found in the README or at r00tuser.com.

Created by: r00
Version: 0.01a
Last modified: 10/2/2020
'''

import csv
import datetime
from gpiozero import Button
from time import sleep

import adafruit_vl53l0x
import board
import busio
import neopixel
import requests
import twitter

import secrets


# Twitter api object.
api = twitter.Api(consumer_key=secrets.consumer_key,
                  consumer_secret=secrets.consumer_secret,
                  access_token_key=secrets.access_token_key,
                  access_token_secret=secrets.access_token_secret)
      
# Setup status LEDs.              
pixels = neopixel.NeoPixel(board.D12, 1, auto_write=True, brightness=0.2, pixel_order=neopixel.RGB)

# Status LED colors.
RED = 0xFF0000
AMBER = 0xFFFF00
GREEN = 0x00FF00
BLUE = 0x00FFFF

# Setup I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Time of flight sensor. Used for measuring standing vs sitting posture.
piss_shit_sensor = adafruit_vl53l0x.VL53L0X(i2c)
piss_shit_sensor.measurement_timing_budget = 200000

def generate_session_message(times):
    minutes = times[2]
    seconds = times[3]
    
    session_type = get_session_type()
    
    if session_type == 'shit':
        return f'I pooped for {minutes} minutes and {seconds} seconds.'
    
    return f'I peed for {minutes} minutes and {seconds} seconds.'
    
def calculate_times(start, end):
    time_delta = end - start
    minutes = (time_delta.seconds // 60) % 60
    seconds = time_delta.seconds - (minutes * 60)
    
    start_str = start.strftime('%m/%d/%Y %H:%M:%S')
    end_str = end.strftime('%m/%d/%Y %H:%M:%S')
    
    return (start_str, end_str, minutes, seconds, start, end)

def tweet(message):
    pixels[0] = BLUE
    status = api.PostUpdate(message)
    pixels[0] = GREEN
    print(status.text)
    
def save_data(times):
    start_time = times[4].strftime('%m/%d/%Y %H:%M:%S')
    end_time = times[5].strftime('%m/%d/%Y %H:%M:%S')
    with open('stats.csv', 'a') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow([start_time, end_time, times[2], times[3], times[4]])
        
def connected_to_internet():
    '''Checks if the system is connected to the internet.'''
    with requests.Session() as session:
        response = session.get('http://www.google.com')
        if response.status_code == 200:
            return True
        else:
            return False
            
def get_session_type():
    '''Determine type of bathroom session.'''
    poop_threshold = 200
    
    distance_to_cheeks = piss_shit_sensor.range
    print(f'Distance to cheeks at time of session end: {distance_to_cheeks}mm.')
    if distance_to_cheeks > poop_threshold:
        return 'piss'
    else:
        return 'shit'

if __name__ == '__main__':
    ass_switch = Button(26)

    while True:
        
        while not connected_to_internet():
            print('WiFi signal lost.')
            # Set Wi-Fi LED to orange.
            sleep(1)
        pixels[0] = GREEN
        pixels.show()
        
        print('Waiting for ass.')
        ass_switch.wait_for_press()
        pixels[0] = AMBER
        
        print('Ass found. Starting timer.')
        start = datetime.datetime.now()
        
        print('Waiting for ass to disappear.')
        ass_switch.wait_for_release()
        pixels[0] = GREEN
        
        print('Poof! Ass is gone. Ending timer.')
        end = datetime.datetime.now()
        
        print('Calculating poop session length.')
        times = calculate_times(start, end)
        
        print('Generating tweets with stats.')
        message = generate_session_message(times)
        
        print('Sending tweet.')
        tweet(message)
        
        print('Saving data to file.')
        save_data(times)
    
    sleep(0.1)