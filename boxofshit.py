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
from math import floor
from time import sleep

import board
import neopixel
import requests
import twitter

import secrets


api = twitter.Api(consumer_key=secrets.consumer_key,
                  consumer_secret=secrets.consumer_secret,
                  access_token_key=secrets.access_token_key,
                  access_token_secret=secrets.access_token_secret)
                    
pixels = neopixel.NeoPixel(board.D12, 2, auto_write=True, brightness=0.2, pixel_order=neopixel.RGB)
wifi_led = pixels[0]

AMBER = 0xFFFF00
GREEN = 0x00FF00
BLUE = 0x00FFFF

def generate_session_message(times, session_type):
    minutes = times[2]
    seconds = times[3]
    
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
    wifi_led.fill(BLUE)
    status = api.PostUpdate(message)
    wifi_led.fill(GREEN)
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
            wifi_led.fill(GREEN)
            return True
        else:
            wifi_led.fill(AMBER)
            return False
            
def get_session_type(tof_data):
    '''Determine type of bathroom session.'''
    poop_threshold = 60

    if tof_data < poop_threshold:
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
        
        print('Waiting for ass.')
        ass_switch.wait_for_press()
        wifi_led.fill(AMBER)
        
        print('Ass found. Starting timer.')
        start = datetime.datetime.now()
        
        print('Waiting for ass to disappear.')
        ass_switch.wait_for_release()
        wifi_led.fill(GREEN)
        
        print('Poof! Ass is gone. Ending timer.')
        end = datetime.datetime.now()
        
        print('Determining session type.')
        session_type = get_session_type(59)
        
        print('Calculating poop session length.')
        times = calculate_times(start, end)
        
        print('Generating tweets with stats.')
        message = generate_session_message(times, session_type)
        
        print('Sending tweet.')
        tweet(message)
        
        print('Saving data to file.')
        save_data(times)
    
    sleep(1)