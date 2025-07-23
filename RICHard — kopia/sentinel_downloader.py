import requests
import json
from datetime import datetime, timedelta

def get_quicklooks():
    endpoint = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

    # Zakres dat: ostatnie 30 dni
    today = datetime.utcnow()
    past_date = today - timedelta(days=30)

    # Format ISO
    date_from = past_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    date_to = today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Parametry zapytania
    query = {
        "$filter": f"Collection/Name eq 'SENTINEL-2' and ContentDate/Start gt {date_from} and ContentDate/Start lt {date_to}",
        "$format": "json",
        "$top": 10,
        "$orderby": "ContentDate/Start desc"
    }

    headers = {
        "Accept": "application/json"
    }

    print("Wysyłanie zapytania do Copernicus Data Space...")  # DEBUG

    try:
        response = requests.get(endpoint, headers=headers, params=query)

        print("Status odpowiedzi:", response.status_code)
        print("Treść odpowiedzi (pierwsze 500 znaków):", response.text[:500])  # DEBUG

        if response.status_code == 200:
            try:
                results = response.json()
                print(json.dumps(results, indent=2))  # DEBUG

                features = results.get('value', [])
                quicklooks = []
                for feature in features:
                    entry = {
                        'id': feature['Id'],
                        'title': feature.get('Name', 'Brak nazwy'),
                        'quicklook_url': f"https://dataspace.copernicus.eu/odata/v1/Products('{feature['Id']}')/Nodes('quicklook')/$value",
                        'geometry': feature.get('Footprint', '')
                    }
                    quicklooks.append(entry)
                return quicklooks
            except json.JSONDecodeError as e:
                print("Błąd dekodowania JSON:", e)
                return []
        else:
            print("Błąd zapytania:", response.status_code)
            return []
    except requests.exceptions.RequestException as e:
        print("Błąd połączenia:", e)
        return []
