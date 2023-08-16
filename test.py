import json
from Objects.WeatherParser import WeatherParser
from logger import logger

weather_parser = WeatherParser()

logger.info("-" * 50)
logger.info("SETUP")

logger.info("Reading contacts.json")
with open("contacts.json", "r") as json_file:
    contacts = json.load(json_file)

logger.info(f"Starting to loop through {len(contacts)} contacts")
for contact in contacts:
    contact_name = contact['name']
    contact_locations = contact['locations']
    time_wakes_up = contact['wakes_up']
    contact_settings = contact['settings']

    logger.info("Looping through contact's locations")
    for _, contact_location_address in contact_locations.items():

        logger.info(f"Run weather parsing "
                    f"on {'NOW'} @ {contact_location_address} for {contact_name}")

        weather_parser.send_morning_notifications(
            contact_location_address,
            contact_name,
            contact_settings
        )

# logger.info("-" * 50)
# logger.info("Schedulers set. Waiting for jobs....")
# while True:
#     schedule.run_pending()
#     time.sleep(1)
