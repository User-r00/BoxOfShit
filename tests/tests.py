#!/usr/bin/ent python3
# -*- coding: utf-8 -*-
from datetime import datetime
import unittest
from unittest.mock import patch
import requests

from boxofshit import (
    calculate_times,
    connected_to_internet,
    generate_session_message,
    tweet
)

class TestBoxOfShit(unittest.TestCase):

    @patch('requests.Session.get', autospec=True)
    def test_connected_to_internet_success(self, mock_get):
        connected_to_internet()
        mock_get.assert_called_once()
        
    @patch('twitter.Api.PostUpdate')
    def test_tweet(self, mock_api_post_update):
        tweet('foo')
        mock_api_post_update.assert_called_once()
        
    def test_generate_session_message(self):
        times = (0, 1, 2, 3, 4, 5)
        message = generate_session_message(times)
        expected_message = 'I pooped for 2 minutes and 3 seconds.'
        
        self.assertEqual(message, expected_message)
        

if __name__ == '__main__':
    unittest.main()