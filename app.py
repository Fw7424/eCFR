from flask import Flask, render_template
from models import db, Agency, Title, AgencyTitle, Correction
from sqlalchemy import func
from collections import defaultdict
import json
from collections import defaultdict
import re

def verify_agency_checksums():
    print("🔍 Verifying agency data integrity...")
    changed = []

    agencies = Agency.query.all()
    for agency in agencies:
        if agency.has_changed():
            changed.append(agency)

    if changed:
        print(f"⚠️ {len(changed)} agencies have changed data!")
        for a in changed:
            print(f" - ID {a.id}: {a.short_name} ({a.name})")
    else:
        print("✅ All agency data checksums verified.")

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agencies.db'  # adjust path if needed
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        db.create_all()
        verify_agency_checksums()


    @app.route("/old")
    def corrections_summary():
        from sqlalchemy import func
        from models import Title, Correction

        # Summary count by title
        summary = (
            db.session.query(
                Title.id,
                Title.name,
                func.count(Correction.id).label("total_corrections")
            )
            .join(Correction, Title.id == Correction.title_id)
            .group_by(Title.id, Title.name)
            .order_by(func.count(Correction.id).desc())
            .all()
        )

        # Get detailed breakdown for each title
        detailed = (
            db.session.query(
                Correction.title_id,
                Correction.year,
                Correction.subtitle,
                Correction.chapter,
                Correction.part,
                Correction.subpart,
                Correction.section,
                func.count(Correction.id).label("count")
            )
            .group_by(
                Correction.title_id,
                Correction.year,
                Correction.chapter,
                Correction.subtitle,
                Correction.part,
                Correction.subpart,
                Correction.section
            )
            .order_by(Correction.title_id, Correction.year)
            .all()
        )

        # Organize by title_id for fast lookup in template
        breakdown_lookup = {}
        for row in detailed:
            breakdown_lookup.setdefault(row.title_id, []).append(row)

        return render_template(
            "c.html",
            summary=summary,
            breakdown_lookup=breakdown_lookup
        )

    def natural_key(text):
        """Sort helper that treats numbers in strings as numbers."""
        return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', text or "")]

    @app.route("/")
    def corrections_summary3():
        titles = Title.query.all()
        result = []

        for title in titles:
            groups = defaultdict(list)

            for corr in title.corrections:
                label = None
                value = None

                # Prioritized hierarchy
                if corr.subtitle:
                    label, value = "Subtitle", corr.subtitle
                elif corr.chapter:
                    label, value = "Chapter", corr.chapter
                elif corr.part:
                    label, value = "Part", corr.part
                elif corr.subpart:
                    label, value = "Subpart", corr.subpart
                elif corr.section:
                    label, value = "Section", corr.section
                elif corr.year:
                    label, value = "Year", str(corr.year)
                else:
                    label, value = "Uncategorized", "N/A"

                key = f"{label}: {value}"

                groups[key].append({
                    "section": corr.section,
                    "year": corr.year or "Unknown",
                    "fr_citation": corr.fr_citation,
                    "action": corr.corrective_action,
                })

            # Sort keys naturally
            sorted_grouped = sorted(groups.items(), key=lambda item: natural_key(item[0]))

            result.append({
                "id": title.id,
                "name": title.name,
                "total": len(title.corrections),
                "grouped": sorted_grouped
            })

        return render_template("index.html", titles=result)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)