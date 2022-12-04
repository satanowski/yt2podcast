# pylint: disable=too-few-public-methods

from pathlib import Path

from loguru import logger as log
from peewee import (
    AutoField,
    BooleanField,
    CharField,
    ForeignKeyField,
    Model,
    SqliteDatabase,
    TimestampField,
)

DB_FILE = Path(__name__).parent / "data.sqlite"
EP_STATES = ("enqueued", "downloading", "downloaded", "processing", "processed", "sent")

db = SqliteDatabase(DB_FILE)


class BaseModel(Model):
    class Meta:
        database = db


class Subscription(BaseModel):
    uuid = CharField(unique=True, max_length=24, primary_key=True)
    name = CharField(unique=True)
    active = BooleanField(default=True)
    last_check = TimestampField(null=True, default=None)


class EpisodeState(BaseModel):
    id = AutoField()
    name = CharField(unique=True)


class Episode(BaseModel):
    name = CharField(unique=True)
    uuid = CharField(unique=True, max_length=12, primary_key=True)
    pub_date = TimestampField(index=True)
    path = CharField(unique=True, null=True)
    state = ForeignKeyField(EpisodeState, default=1)


def initialize_db():
    log.debug(f"Initializing database file ({DB_FILE.as_posix()})")
    db.connect()
    db.create_tables([Subscription, EpisodeState, Episode])
    for state in EP_STATES:
        EpisodeState.create(name=state).save()
    db.close()


if not DB_FILE.exists():
    initialize_db()
