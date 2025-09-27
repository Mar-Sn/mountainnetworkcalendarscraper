import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz

# URL van de Mountain Network agenda
url = "https://mountain-network.nl/klimcentra/agenda/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# Define the locations to filter by
LOCATIONS = ['Leeuwarden', 'Heerenveen', 'Rijnboulder', 'Nieuwegein']


def scrape_mountain_network():
    """ Scrapes event data from the Mountain Network agenda page. """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for request errors
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all event items
        events = soup.find_all('article', class_='card--agenda')

        event_data = []
        for event in events:
            title_element = event.find('h3', class_='card__hd')
            date_element = event.find('time', class_='cal-item')
            location_element = event.find('div', class_='card__meta')
            link_element = event.find('a', href=True)

            if title_element and date_element and location_element and link_element:
                title = title_element.get_text(strip=True)
                date_str = date_element['datetime']
                location = location_element.get_text(strip=True).replace('Locatie:', '').strip()
                link = link_element['href']

                # Assuming the date is in 'DD-MM-YYYY' format and adding a default time
                # Mountain Network doesn't provide specific times on the main agenda page
                try:
                    event_date = datetime.strptime(date_str, '%d-%m-%Y')
                    event_data.append({
                        'summary': title,
                        'dtstart': event_date,
                        'location': location,
                        'description': f"Meer info: {link}"
                    })
                except ValueError:
                    print(f"Skipping event with unparsable date: {date_str}")

        return event_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return []


def filter_events_by_location(events, target_location):
    """ Filter events that match the target location (case-insensitive partial match). """
    filtered_events = []
    for event in events:
        # Check if the target location is contained in the event location (case-insensitive)
        if target_location.lower() in event['location'].lower():
            filtered_events.append(event)
    return filtered_events


def create_ical(events, filename):
    """ Creates an iCalendar file from a list of events. """
    if not events:
        print(f"No events found for {filename}. Skipping file creation.")
        return
    
    cal = Calendar()
    cal.add('prodid', '-//Mountain Network Agenda//mxm.dk//')
    cal.add('version', '2.0')

    amsterdam_tz = pytz.timezone('Europe/Amsterdam')

    for event_details in events:
        event = Event()
        event.add('summary', event_details['summary'])

        # Set start and end time (assuming all-day event if no time is specified)
        # The calendar will handle this as an all-day event
        event.add('dtstart', event_details['dtstart'].date())
        event.add('dtend', (event_details['dtstart'] + timedelta(days=1)).date())

        event.add('dtstamp', datetime.now(amsterdam_tz))
        event.add('location', event_details['location'])
        event.add('description', event_details['description'])
        event.add('uid',
                  f"{event_details['dtstart'].strftime('%Y%m%d')}-{event_details['summary']}@mountain-network.nl")

        cal.add_component(event)

    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    print(f"{filename} file created successfully with {len(events)} events.")


def main():
    scraped_events = scrape_mountain_network()
    if scraped_events:
        print(f"Total events scraped: {len(scraped_events)}")
        
        # Create separate calendars for each location
        for location in LOCATIONS:
            location_events = filter_events_by_location(scraped_events, location)
            filename = f"agenda_{location.lower()}.ics"
            create_ical(location_events, filename)
        
        # Also create a combined calendar with all events
        create_ical(scraped_events, 'agenda_all.ics')
        
        print("\nLocation-specific calendar files created:")
        for location in LOCATIONS:
            print(f"- agenda_{location.lower()}.ics")
        print("- agenda_all.ics (combined)")

if __name__ == "__main__":
    main()