import base64
import time

import requests
import os
from dotenv import load_dotenv
from logger import logger
import json
import datetime

load_dotenv()


class WeatherParser:

    def __init__(self):
        self.API_KEY = os.getenv("OPEN_WEATHER_MAP_API_KEY")
        self.NOTIFICATION_APP_AUTH_KEY = os.getenv("NOTIFICATION_APP_AUTH_KEY")
        self.data = None
        self.file_name = "weather_data.json"
        self.icon_attachment_type = 'image/png'

    def push_notification(self, notification: dict):

        push_url = os.getenv("PUSH_URL")
        # Headers for the request
        headers = {
            'auth-key': self.NOTIFICATION_APP_AUTH_KEY
        }

        data = {
            'notification': json.dumps(notification),
            'application': 'umbrella'
        }

        response = requests.post(push_url, headers=headers, data=data)
        return response

    # ----- WEATHER methods
    def get_weather_forecast(self, latitude, longitude) -> bool:
        request_url = "https://api.openweathermap.org/data/2.5/onecall"
        max_retries = 3
        retries = 0

        while retries < max_retries:
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.API_KEY,
                'units': 'metric',
                'lang': 'lt'
            }

            response = requests.get(request_url, params=params)

            if response.status_code == 200:
                data = response.json()
                self.data = data
                return True

            else:
                logger.info(f"Request failed with status code: {response.status_code}")
                retries += 1
                if retries < max_retries:
                    logger.info(f"Retrying in 5 seconds...")
                    time.sleep(5)

        logger.info("Max retries reached. Unable to fetch data.")
        return False

    @staticmethod
    def get_icon_base64(icon_code):
        base_url = "https://openweathermap.org/img/wn/"
        icon_url = f"{base_url}{icon_code}@2x.png"

        # Download the icon and convert to base64
        response = requests.get(icon_url)
        if response.status_code == 200:
            icon_data = response.content
            attachment_base64 = base64.b64encode(icon_data).decode('utf-8')
            return attachment_base64

        else:
            return None

    # ----- SEND methods
    def send_morning_alert(self, latitude: float, longitude: float, contact_name: str):

        logger.info(f"Sending morning alert for {contact_name}")

        self.get_weather_forecast(latitude, longitude)
        current_data = self.data['current']

        current_temp = current_data['temp']
        feels_like = current_data['feels_like']
        wind_speed = current_data['wind_speed']

        current_weather = current_data['weather'][0]
        weather_id = current_weather['id']
        weather_desc = current_weather['description']
        weather_icon = current_weather['icon']

        notification_message = f"{weather_desc} - {current_temp}C " \
                               f"(feels like: {feels_like}C). Wind: {wind_speed} m/s"
        notification = {
            "group": os.getenv("UMBRELLA_GROUP"),
            "message": notification_message,
            "title": "UMBRELLA: Current Weather",
            "attachment_base64": self.get_icon_base64(weather_icon),
            "attachment_type": self.icon_attachment_type,
            "priority": 0,
        }

        response = self.push_notification(notification)
        logger.info(f"Sending notification to {contact_name} result: {response.status_code}, {response.text}")
        return response

    # ----- DATE / TIMESTAMP methods
    @staticmethod
    def convert_utc_to_local_timestamp(utc_timestamp, timezone_offset):
        utc_datetime = datetime.datetime.utcfromtimestamp(utc_timestamp)
        local_datetime = utc_datetime + datetime.timedelta(seconds=timezone_offset)
        local_timestamp = int(local_datetime.timestamp())
        return local_timestamp

    @staticmethod
    def timestamp_to_human_readable(timestamp):
        return datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # ----- FILE methods
    def write_data_to_file(self):
        with open(self.file_name, "w") as outfile:
            json.dump(self.data, outfile, indent=4)

    def read_data_from_file(self):
        with open(self.file_name, 'r') as infile:
            return json.load(infile)
