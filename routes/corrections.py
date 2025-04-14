from flask import render_template
from models import db, Title, Correction
from sqlalchemy import func

@app.route("/corrections/summary")
def corrections_summary():
    # Total corrections per title
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

    # Corrections broken down by title and year
    breakdown = (
        db.session.query(
            Correction.title_id,
            Correction.year,
            func.count(Correction.id).label("count")
        )
        .group_by(Correction.title_id, Correction.year)
        .order_by(Correction.title_id, Correction.year)
        .all()
    )

    # Group breakdown by title for quick lookup in template
    year_lookup = {}
    for row in breakdown:
        year_lookup.setdefault(row.title_id, []).append((row.year, row.count))

    return render_template("corrections_summary.html", summary=summary, year_lookup=year_lookup)
