import base64
import time
import requests
import os
from dotenv import load_dotenv
from geopy import Nominatim
from logger import logger
import json
import datetime


load_dotenv()


class WeatherParser:

    def __init__(self):

        self.address_parsed = None
        self.parsed_ts = None

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
    def get_weather_forecast(self, address: str) -> bool:
        request_url = "https://api.openweathermap.org/data/2.5/onecall"
        max_retries = 3
        retries = 0

        latitude, longitude = self.address_to_latlng(address)

        if latitude is None or longitude is None:
            logger.info("Received None from address_to_latlng()")
            logger.info("Returning False from get_weather_forecast()")
            return False

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
                data['address'] = address

                self.data = data
                self.address_parsed = address
                self.parsed_ts = self.convert_utc_to_local_timestamp(
                    utc_timestamp=data['current']['dt'], timezone_offset=data['timezone_offset'])
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
    def send_morning_current_weather_notification(self, contact_name: str):

        logger.info(f"Generating morning current weather notification for {contact_name}")
        address = self.data['address']
        timezone_offset = self.data['timezone_offset']
        current_data = self.data['current']

        today_ts = self.convert_utc_to_local_timestamp(current_data['dt'], timezone_offset)
        today_dt = datetime.datetime.fromtimestamp(today_ts)

        current_temp = current_data['temp']
        feels_like = current_data['feels_like']
        clouds = current_data['clouds']
        wind_speed = current_data['wind_speed']
        uv_index = current_data['uvi']

        current_weather = current_data['weather'][0]
        weather_desc = current_weather['description']

        notification_message = f"{weather_desc.capitalize()}:\n" \
                               f" Current temperature: {current_temp} C\n" \
                               f" Feels like: {feels_like} C \n" \
                               f" Clouds: {clouds}% \n" \
                               f" Current UV index: {uv_index} \n" \
                               f" Wind speed: {wind_speed} m/s \n"
        notification = {
            "group": os.getenv("UMBRELLA_GROUP"),
            "message": notification_message,
            "title": f"Current weather ({today_dt.strftime('%m-%d %H:%M:%S')}) @ {address}",
            "priority": 0,
        }

        logger.info(f"Notification generated successfully: {notification}, pushing...")
        response = self.push_notification(notification)
        logger.info(f"Pushed morning current weather notification to {contact_name}, "
                    f"result: {response.status_code}, {response.text}")
        return response

    def send_morning_day_weather_notification(self, contact_name):

        logger.info(f"Generating morning day weather notification for {contact_name}")
        timezone_offset = self.data['timezone_offset']
        address = self.data['address']

        data_today = self.data['daily'][0]

        percentage_of_rain = data_today['pop'] * 100
        cloud_percentage = data_today['clouds']
        wind_speed = data_today['wind_speed']
        max_uv_index = data_today['uvi']
        max_uv_index_time = "could not find"

        # find when the max uv index is hitting
        hourly_data_list = self.data['hourly']
        today_ts = self.convert_utc_to_local_timestamp(data_today['dt'], timezone_offset)
        today_dt = datetime.datetime.fromtimestamp(today_ts)
        today_day = today_dt.day

        for hourly_data in hourly_data_list:
            hourly_data_ts = self.convert_utc_to_local_timestamp(hourly_data['dt'], timezone_offset)
            hourly_day = datetime.datetime.fromtimestamp(hourly_data_ts).day

            if hourly_day != today_day:
                break

            if hourly_data['uvi'] == max_uv_index:
                max_uv_index_dt = datetime.datetime.fromtimestamp(hourly_data_ts)
                max_uv_index_time = max_uv_index_dt.strftime('%H:%M')

        feels_like_data = data_today['feels_like']

        weather_data = data_today['weather'][0]
        weather_desc = weather_data['description']

        notification_message = f"{weather_desc.capitalize()}:\n" \
                               f" Rain chance: {percentage_of_rain}% \n" \
                               f" Clouds: {cloud_percentage}% \n" \
                               f" Max UV index: {max_uv_index} @ {max_uv_index_time} \n" \
                               f" Wind speed: {wind_speed} m/s \n" \
                               f" Temperature will feel like: \n" \
                               f" \t - morning: {feels_like_data['morn']}\n " \
                               f" \t - day: {feels_like_data['day']}\n " \
                               f" \t - evening: {feels_like_data['eve']}\n " \
                               f" \t - night: {feels_like_data['night']}\n "

        notification = {
            "group": os.getenv("UMBRELLA_GROUP"),
            "message": notification_message,
            "title": f"Today's weather ({today_dt.strftime('%m-%d')}) @ {address}",
            "priority": 0,
        }

        logger.info(f"Notification generated successfully: {notification}, pushing...")
        response = self.push_notification(notification)
        logger.info(f"Pushed upcoming day weather notification to {contact_name}, "
                    f"result: {response.status_code}, {response.text}")

    def send_morning_notifications(self, address, contact_name, settings):

        logger.info(f"Starting to generate morning notifications for {contact_name} @ {address}")

        success = self.get_weather_forecast(address)

        if not success:
            logger.error(f"Failed to get weather forecast for {contact_name} @ {address}")
            logger.info("Exiting method without sending anything")
            return

        logger.info(f"Got weather forecast for {contact_name} @ {address}")

        # for debug
        self.write_data_to_file()

        logger.info(f"Check if {contact_name} has enabled 'morning_current_weather_notification'")
        if settings["morning_current_weather_notification"]:
            logger.info("'morning_current_weather_notification' enabled - generating current weather notification")
            self.send_morning_current_weather_notification(contact_name)

        logger.info(f"Check if {contact_name} has enabled 'morning_day_weather_notification'")
        if settings["morning_day_weather_notification"]:
            logger.info("'morning_day_weather_notification' enabled - generating upcoming day weather notification")
            self.send_morning_day_weather_notification(contact_name)

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

    @staticmethod
    def address_to_latlng(address):
        geolocator = Nominatim(user_agent="my_geocoder")

        logger.info(f"Geolocating address: {address}")
        location = geolocator.geocode(address)

        if location:
            logger.info(f"Geolocated location: {location}")
            logger.info(f"Latitude: {location.latitude}, Longitude: {location.longitude}")
            return location.latitude, location.longitude

        else:
            logger.error(f"Failed to geolocate, address used: {address}")
            return None, None

    # ----- FILE methods
    def write_data_to_file(self):
        logger.info(f"Writing self.data to {self.file_name}")
        with open(self.file_name, "w") as outfile:
            json.dump(self.data, outfile, indent=4)

    def read_data_from_file(self):
        logger.info(f"Reading from {self.file_name}")
        with open(self.file_name, 'r') as infile:
            return json.load(infile)
