from pony.orm import Database, Optional, Required, composite_key

BLANK = ""
DECISION_AUTO = "auto"
DECISION_MANUAL_CHOICE = "manual_choice"
DECISION_MANUAL_CHOICE_SKIPPED = "manual_choice_skipped"
DECISION_MANUAL_ENTRY = "manual_entry"

db = Database()


def connect_db(filename: str = 'fetched-metadata.sqlite'):
    db.bind(provider='sqlite', filename=filename, create_db=True)
    db.generate_mapping(create_tables=True)

class MusicBrainzDetails(db.Entity):
    searched_title = Required(str)
    searched_artist = Required(str)
    musicbrainz_id = Optional(str)
    musicbrainz_json = Optional(str)
    # Only use the DECISION_[whatever] entries
    match_decision_source = Required(str, index=True)

    # Make searching on this fast + make it unique
    composite_key(searched_title, searched_artist)
