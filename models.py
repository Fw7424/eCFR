from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import hashlib

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agencies.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

class Title(db.Model):
    __tablename__ = 'titles'

    id = db.Column(db.Integer, primary_key=True)  # Title number, e.g., 1
    name = db.Column(db.String(255), nullable=False)  # Title name from API

    agencies = db.relationship('AgencyTitle', back_populates='title')
    corrections = db.relationship('Correction', back_populates='title')
    def __repr__(self):
        return f"<Title {self.name}>"
    
class AgencyTitle(db.Model):
    __tablename__ = 'agency_titles'

    id = db.Column(db.Integer, primary_key=True)
    agency_id = db.Column(db.Integer, db.ForeignKey('agency.id'))
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'))

    agency = db.relationship('Agency', back_populates='titles')
    title = db.relationship('Title', back_populates='agencies')


class Agency(db.Model):
    __tablename__ = 'agency'

    id = db.Column(db.Integer, primary_key=True)
    parent_short_name = db.Column(db.String(255))
    short_name = db.Column(db.String(255))
    name = db.Column(db.String(255))
    slug = db.Column(db.String(255))
    children = db.Column(db.String(255))
    cfr_reference = db.Column(db.PickleType)
    checksum = db.Column(db.String(64))

    def calculate_checksum(self):
        """
        Generate SHA256 checksum from agency data.
        """
        data = f"{self.short_name}|{self.name}|{self.slug}|{self.children}|{self.cfr_reference}|{self.parent_short_name}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def has_changed(self):
        return self.checksum != self.calculate_checksum()
    
    titles = db.relationship('AgencyTitle', back_populates='agency')

class Correction(db.Model):
    __tablename__ = "corrections"

    id = db.Column(db.String, primary_key=True)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'))
    # title_number = db.Column(db.Integer, db.ForeignKey("titles.id"), nullable=True)


    # Link to Title table
    title = db.relationship('Title', back_populates='corrections')
    # title = db.relationship("Title", backref=db.backref("corrections", lazy=True))

    # Top-level fields
    fr_citation = db.Column(db.String(255))
    corrective_action = db.Column(db.Text)
    error_corrected = db.Column(db.Text)
    error_occurred = db.Column(db.Text)
    last_modified = db.Column(db.Text)
    display_in_toc = db.Column(db.Boolean)
    position = db.Column(db.Integer)
    year = db.Column(db.Integer)
    title_text = db.Column(db.Text)  # maps to ecfr_corrections.title

    # cfr_reference and hierarchy
    cfr_reference = db.Column(db.String(255))
    chapter = db.Column(db.String(255))
    part = db.Column(db.String(255))
    section = db.Column(db.String(255))
    subchapter = db.Column(db.String(255))
    subject_group = db.Column(db.String(255))
    subpart = db.Column(db.String(255))
    subtitle = db.Column(db.String(255))



    def __repr__(self):
        return f"<Agency {self.short_name}>"
