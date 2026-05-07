import random
import string

from app.models.models import Album


def generate_unique_album_code(db, length=6):

    while True:

        code = ''.join(
            random.choice(
                string.ascii_uppercase + string.digits
            )
            for _ in range(length)
        )

        existing = db.query(Album).filter(
            Album.album_code == code
        ).first()

        if not existing:
            return code