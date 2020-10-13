#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Box of Shit is a bot that monitors bathroom habits to enlighten and entertain.

BoS is built in Python and designed to run on a Raspberry Pi Zero W. The full
wiring diagram can be found in the README or at r00tuser.com.

Created by: r00
Version: 0.01a
Last modified: 10/2/2020


             -----
            | 1|2 |
    ToF SDA | 3|4 | Neopixel 5V
    ToF SCL | 5|6 | Neopixel Ground
            | 7|8 |
            | 9|10|
            |11|12|
            |13|14|
            |15|16|
            |17|18|
            |19|20|
            |21|22|
            |23|24|
            |25|26| Trigger Button
            |27|28|
            |29|30|
            |31|32| Neopixels
            |33|34|
            |35|36|
            |37|38|
            |39|40|
             -----
'''

import csv
import datetime
from random import randint
from time import sleep

import adafruit_vl53l0x
import board
import busio
from gpiozero import Button
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
# Power  = 0
# Status = 1
pixels = neopixel.NeoPixel(board.D12,
                           2,
                           auto_write=True,
                           brightness=0.2,
                           pixel_order=neopixel.RGB)

# Status LED colors.
RED = (255, 0, 0)
AMBER = (255, 255, 0)
ORANGE = (255, 90, 0)
GREEN = (0, 255, 0)
BLUE = (0, 255, 255)
CLEAR = (0, 0, 0)

# Setup I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Time of flight sensor. Used for measuring standing vs sitting posture.
piss_shit_sensor = adafruit_vl53l0x.VL53L0X(i2c)
piss_shit_sensor.measurement_timing_budget = 200000


def generate_status_message(times):
    hours = times[2]
    minutes = times[3]
    seconds = times[4]

    session_type = get_session_type()

    if session_type == 'shit':
        status = 'I pooped for '
    else:
        status = 'I peed for '

    if hours > 0:
        status = f'{status}{hours} hours'

    if minutes > 0:
        status = f'{status}{minutes} minutes'

    status = f'{status}{seconds} seconds'

    stats = calculate_stats(times)

    water = stats['water_usage']
    energy = stats['energy_cost']
    status = f'{status} using {water}g of water and {energy}c in energy.'

    return status


def calculate_kwh(wattage, seconds):
    '''Calculate kilowatt hours based on wattage.'''
    # Convert seconds into hours.
    hours = seconds / 60 / 60

    # Calculate and return kWh.
    return wattage * hours / 1000


def calculate_stats(times):
    '''Calculate various stats based on session time.'''
    # Wattage of one Philips Hue bulb at full brightness.
    hue_wattage = 5.4

    # Number of bulbs in the bathroom.
    bulb_count = 1

    # Gallons of water used per flush.
    water_usage = 5

    # kWh of energy used by the bulbs.
    energy_usage = calculate_kwh(hue_wattage * bulb_count, times[4])
    kwh_cost = 0.2437

    # Energy usage in cents.
    energy_cost = round(kwh_cost * energy_usage * 100, 4)

    # Package the data.
    data = {
        'energy_usage': energy_usage,
        'energy_cost': energy_cost,
        'water_usage': water_usage
    }

    return data


def flicker(led: int, duration: int, color: set):
    '''Randomly flicker an LED for a given amount of time.'''
    random_floor = 1
    random_ceiling = 25

    for i in range(duration):
        # light up for that time
        pixels[led] = color

        # get random number
        random_number = float(randint(random_floor, random_ceiling) / 100)

        sleep(random_number)

        # Turn off
        pixels[led] = CLEAR

        # get random number
        random_number = float(randint(random_floor, random_ceiling) / 100)
        sleep(random_number)


def blink(led, color):
    '''Blink an led a given color one time.'''
    pixels[led] = color
    sleep(1)
    pixels[led] = CLEAR
    sleep(1)


def calculate_times(start, end):
    time_delta = end - start
    hours = time_delta.seconds // 3600
    minutes = (time_delta.seconds // 60) % 60
    seconds = time_delta.seconds - (minutes * 60) - (hours * 3600)

    start_str = start.strftime('%m/%d/%Y %H:%M:%S')
    end_str = end.strftime('%m/%d/%Y %H:%M:%S')

    return (start_str, end_str, hours, minutes, seconds, start, end)


def tweet(message):
    # Number of times to retry sending a tweet before giving up.
    retries = 3
    successful_tweet = False

    for retry in range(retries - 1):
        if not successful_tweet:
            pixels[1] = BLUE
            status = api.PostUpdate(message)

            if message not in status.text:
                sleep(3)
            else:
                successful_tweet = True

    flicker(1, 10, (BLUE))


def save_data(times):
    '''Save session data to a file.'''
    with open('stats.csv', 'a') as csvfile:
        csvwriter = csv.writer(csvfile,
                               delimiter=',',
                               quotechar='|',
                               quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow([times[0],
                            times[1],
                            times[2],
                            times[3],
                            times[4],
                            times[5],
                            times[6]])

    flicker(1, 10, AMBER)


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

    if distance_to_cheeks > poop_threshold:
        return 'piss'
    else:
        return 'shit'


if __name__ == '__main__':
    ass_switch = Button(26)

    # Turn on power LED.
    pixels[0] = RED
    pixels[1] = RED

    while True:

        while not connected_to_internet():
            print('WiFi signal lost.')
            blink(1, ORANGE)
        pixels[1] = GREEN

        print('Waiting for ass.')
        ass_switch.wait_for_press()
        pixels[1] = AMBER

        print('Ass found. Starting timer.')
        start = datetime.datetime.now()

        print('Waiting for ass to disappear.')
        ass_switch.wait_for_release()
        pixels[1] = GREEN

        print('Poof! Ass is gone. Ending timer.')
        end = datetime.datetime.now()

        print('Calculating poop session length.')
        times = calculate_times(start, end)

        print('Generating tweets with stats.')
        message = generate_status_message(times)

        print('Sending tweet.')
        tweet(message)

        print('Saving data to file.')
        save_data(times)

    # Turn off power LED. We should never get here but...ya know...
    while True:
        pixels[0] = RED
        sleep(1)
        pixels[0] = CLEAR
        sleep(1)
