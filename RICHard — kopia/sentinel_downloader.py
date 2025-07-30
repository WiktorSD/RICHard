import requests
from datetime import datetime, timedelta

def get_sentinel_quicklook(corners, satellite="sentinel1"):
    endpoint = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

    # Wybór kolekcji satelity
    collection = "SENTINEL-1" if satellite.lower() == "sentinel1" else "SENTINEL-2"

    # Budowa WKT (Well-Known Text) - prostokąt
    polygon_wkt = (
    f"POLYGON(({corners['nw']['lon']} {corners['nw']['lat']}, "
    f"{corners['ne']['lon']} {corners['ne']['lat']}, "
    f"{corners['se']['lon']} {corners['se']['lat']}, "
    f"{corners['sw']['lon']} {corners['sw']['lat']}, "
    f"{corners['nw']['lon']} {corners['nw']['lat']}))"
)



    # Daty: od 30 dni wstecz do teraz
    today = datetime.utcnow()
    past_date = today - timedelta(days=30)

    date_from = past_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    date_to = today.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Escapowanie apostrofów w WKT
    polygon_wkt_escaped = polygon_wkt.replace("'", "''")

    # Budowanie zapytania
    query = {
        "$filter": (
            f"Collection/Name eq '{collection}' and "
            f"OData.CSC.Intersects(area=geography' {polygon_wkt_escaped}') and "
            f"ContentDate/Start gt {date_from} and "
            f"ContentDate/Start lt {date_to}"
        ),
        "$top": 1,
        "$orderby": "ContentDate/Start desc",
        "$format": "json"
    }

    headers = {
        "Accept": "application/json"
    }

    # DEBUG
    print("📌 Data from:", date_from)
    print("📌 Data to:", date_to)
    print("📐 POLYGON WKT:", polygon_wkt)
    print("🛰️ Satelita:", satellite)
    print("🌐 Zapytanie:", query)

    try:
        response = requests.get(endpoint, headers=headers, params=query, timeout=15)

        print("📦 API status:", response.status_code)

        if response.status_code != 200:
            print(f"❌ Błąd API ({satellite}):", response.text)
            return None

        data = response.json()
        features = data.get("value", [])
        print(f"📦 Produkty: {len(features)}")

        if not features:
            print(f"🔍 Brak danych Sentinel dla tego obszaru ({satellite})")
            return None

        feature = features[0]
        product_id = feature.get("Id")
        product_name = feature.get("Name")

        quicklook_url = f"https://dataspace.copernicus.eu/odata/v1/Products('{product_id}')/Nodes('quicklook')/$value"

        print("✅ Znaleziony produkt:", product_name)
        print("🖼️ Quicklook URL:", quicklook_url)

        return {
            "title": product_name,
            "quicklook_url": quicklook_url
        }

    except Exception as e:
        print("❌ Wyjątek API:", e)
        return None
