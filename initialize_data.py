import requests
from datetime import datetime
import json
from models import create_app, db, Title, Agency, AgencyTitle, Correction

BASE_URL = "https://www.ecfr.gov"

# --- ECFR Client and Save Agencies ---
class ECFRClient:
    def __init__(self, timeout=10):
        self.session = requests.Session()
        self.timeout = timeout

    def get_agencies(self):
        url = f"{BASE_URL}/api/admin/v1/agencies.json"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

def save_agencies(agencies_data):
    agencies = agencies_data.get("agencies", [])
    total_saved = 0

    for item in agencies:
        total_saved += insert_agency(item, parent_short_name=None)
        for child in item.get("children", []):
            total_saved += insert_agency(child, parent_short_name=item.get("short_name"))

    db.session.commit()
    print(f"✅ {total_saved} agencies (including children) saved to agencies.db")

def insert_agency(data, parent_short_name=None):
    short_name = data.get("short_name")
    name = data.get("name")
    slug = data.get("slug")
    cfr_reference = data.get("cfr_references", [])

    if not short_name:
        return 0

    existing = Agency.query.filter_by(short_name=short_name).first()
    if not existing:
        agency = Agency(
            parent_short_name=parent_short_name or short_name,
            short_name=short_name,
            name=name,
            slug=slug,
            cfr_reference=cfr_reference
        )

        agency.checksum = agency.calculate_checksum()
        db.session.add(agency)
        print(f"➕ Added: {name} ({'child of ' + parent_short_name if parent_short_name else 'parent'})")
        return 1
    return 0

# --- Titles ---
def populate_titles():
    print("📥 Fetching CFR titles...")
    url = f"{BASE_URL}/api/versioner/v1/titles.json"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception("Failed to fetch titles from eCFR")

    data = res.json()
    count = 0

    for item in data["titles"]:
        title_number = item.get("title_number")
        name = item.get("title_name")

        if not title_number or not name:
            continue

        existing = Title.query.get(title_number)
        if not existing:
            db.session.add(Title(id=title_number, name=name))
            count += 1

    db.session.commit()
    print(f"✅ {count} titles saved to the database.")

# --- Agency/Title Relationships ---
def associate_agencies_to_titles():
    print("🔗 Associating agencies with titles...")

    agencies = Agency.query.all()
    links_created = 0

    for agency in agencies:
        refs = agency.cfr_reference or []
        if isinstance(refs, str):
            try:
                refs = json.loads(refs)
            except Exception:
                continue

        for ref in refs:
            title_num = ref.get("title")
            if not title_num:
                continue

            title = Title.query.get(int(title_num))
            if not title:
                continue

            existing_link = AgencyTitle.query.filter_by(agency_id=agency.id, title_id=title.id).first()
            if not existing_link:
                link = AgencyTitle(agency_id=agency.id, title_id=title.id)
                db.session.add(link)
                links_created += 1

    db.session.commit()
    print(f"✅ {links_created} agency-title links created.")

# --- Corrections ---
class CorrectionClient:
    def __init__(self, timeout=10):
        self.session = requests.Session()
        self.timeout = timeout

    def get_corrections(self):
        url = f"{BASE_URL}/api/admin/v1/corrections.json"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching corrections: {e}")
            return None

def save_corrections(data):
    corrections = data.get("ecfr_corrections", [])
    total_saved = 0

    for item in corrections:
        correction_id = item.get("id")
        if not correction_id:
            continue

        cfr_ref = item.get("cfr_references", [{}])[0]
        hierarchy = cfr_ref.get("hierarchy", {})
        title_id = hierarchy.get("title")

        if not title_id:
            continue

        existing = Correction.query.get(correction_id)
        if existing:
            continue

        correction = Correction(
            id=correction_id,
            title_id=title_id,
            fr_citation=item.get("fr_citation"),
            corrective_action=item.get("corrective_action"),
            error_corrected=item.get("error_corrected"),
            error_occurred=item.get("error_occurred"),
            last_modified=item.get("last_modified"),
            display_in_toc=item.get("display_in_toc", False),
            position=item.get("position"),
            year=item.get("year"),
            title_text=item.get("title"),
            cfr_reference=cfr_ref.get("cfr_reference"),
            chapter=hierarchy.get("chapter"),
            part=hierarchy.get("part"),
            section=hierarchy.get("section"),
            subchapter=hierarchy.get("subchapter"),
            subject_group=hierarchy.get("subject_group"),
            subpart=hierarchy.get("subpart"),
            subtitle=hierarchy.get("subtitle"),
        )

        db.session.add(correction)
        print(f"➕ Added correction: {correction_id} (Title {title_id})")
        total_saved += 1

    db.session.commit()
    print(f"✅ {total_saved} corrections saved to database.")

# --- Main Runner ---
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        print("🚀 Starting eCFR data initialization...")

        # Step 1: Save agencies
        ecfr = ECFRClient()
        data = ecfr.get_agencies()
        if data:
            save_agencies(data)
        else:
            print("❌ Failed to fetch agency data.")
            exit(1)

        # Step 2: Save CFR titles
        populate_titles()

        # Step 3: Create relationships
        associate_agencies_to_titles()

        # Step 4: Fetch and save corrections
        client = CorrectionClient()
        corrections_data = client.get_corrections()
        if corrections_data:
            save_corrections(corrections_data)
        else:
            print("❌ No corrections data fetched.")

        print("🏁 All data successfully initialized.")
