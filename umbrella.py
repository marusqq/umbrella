import json
import time
import schedule
from Objects.WeatherParser import WeatherParser
from logger import logger

weather_parser = WeatherParser()

logger.info("Reading contacts.json")
with open("contacts.json", "r") as json_file:
    contacts = json.load(json_file)

logger.info(f"Starting to loop through {len(contacts)} contacts")
for contact in contacts:

    contact_name = contact['name']
    contact_location = contact['location']
    latitude = contact_location['latitude']
    longitude = contact_location['longitude']
    time_wakes_up = contact['wakes_up']

    logger.info(f"Scheduling morning alert for {contact_name} @ {time_wakes_up} in location {latitude}, {longitude}")
    schedule.every().day.at(time_wakes_up).do(weather_parser.send_morning_alert, latitude, longitude, contact_name)

    # weather_parser.send_morning_alert()
    # weather_parser.get_weather_forecast(lat, lon)
    # weather_parser.write_data_to_file()
    # weather_parser.read_data_from_file()


logger.info("Schedulers set. Waiting for jobs....")
while True:
    schedule.run_pending()
    time.sleep(1)




