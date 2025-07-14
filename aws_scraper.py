import json
import os
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values, load_dotenv

load_dotenv() 

CURRENT_DATE = datetime.today().strftime('%d.%m.20%y')
CURRENT_YEAR = datetime.today().strftime('20%y')
BASE_URL = "https://service.stuttgart.de/lhs-services/aws/abfuhrtermine"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
# Change to your street and house number
ADDRESS = {
    "calendar[street]": os.getenv("STREET"),
    "calendar[streetnr]": os.getenv("STREETNR"),
    "calendar[datefrom]": f"01.01.{CURRENT_YEAR}",
    "calendar[dateto]": f"31.01.{int(CURRENT_YEAR)+1}",
    "calendar[wastetype][]": ["restmuell", "biomuell", "altpapier", "gelbersack"],
    "calendar[submit]": "Abfuhrtermine ermitteln"
}
FILENAME = f"{CURRENT_YEAR}_abfuhrtermine.json"

def scrape_abfuhrtermine():
    session = requests.Session()
    response = session.post(BASE_URL, headers=HEADERS, data=ADDRESS)
    soup = BeautifulSoup(response.text, "html.parser")

    results = {}
    current_type = None

    rows = soup.select("table#awstable tr")
    for row in rows:
        header = row.find("th")
        if header:
            # Extract internal value like "restmuell", "biomuell" from text
            text = header.text.strip().lower()
            if "restabfall" in text:
                current_type = "restmuell"
            elif "bioabfall" in text:
                current_type = "biomuell"
            elif "altpapier" in text:
                current_type = "altpapier"
            elif "gelber sack" in text:
                current_type = "gelbersack"
            else:
                current_type = text  # fallback
            results[current_type] = []
        else:
            cols = row.find_all("td")
            if len(cols) >= 2 and current_type:
                date = cols[1].text.strip()
                results[current_type].append(date)

    return results


def save_json(data):
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {FILENAME}")
    
    
def update_and_save_abfuhrtermine():
    if not os.path.exists(FILENAME):
        deprecated_file = f"{int(CURRENT_YEAR)-1}_abfuhrtermine.json"
        if os.path.exists(deprecated_file):
            os.remove(deprecated_file)
            print(f"Deleted deprecated file: {deprecated_file}")
        
    new_data = scrape_abfuhrtermine()
    save_json(new_data)
    print(f"Created new file {FILENAME} with {len(new_data)} entries.")

def check_tomorrow_matches():
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%Y")

    with open(FILENAME) as f: 
        data = json.load(f)
        matched_types = []
        for type, dates in data.items():
            if tomorrow in dates:
                matched_types.append(type)
                continue
    print("Tomorrow is the day for: ", matched_types)
    return matched_types


if __name__ == "__main__":
    update_and_save_abfuhrtermine()
    check_tomorrow_matches()