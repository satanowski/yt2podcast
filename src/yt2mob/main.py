#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path

import click
from loguru import logger as log
import peewee

from models import Episode, EpisodeState, Subscription, db
from yt import download_and_process, get_channel_entries, get_channel_name
from s3 import send2bucket


@click.group()
def cli():
    pass


@click.command()
@click.argument("uid", nargs=-1)
def sub(uid):
    db.connect()
    for channel_id in uid:
        name = get_channel_name(channel_id)
        log.info(f'Adding channel: "{name}"')
        Subscription.create(uuid=channel_id, name=name).save()
    db.close()


@click.command()
def list_sub():
    db.connect()
    for channel in Subscription.select():
        uid = click.style(channel.uuid, fg="green", bold=True)
        name = click.style(channel.name, fg="white")
        click.echo(f"{uid}\t{channel.last_check or '-'}\t{name}")
    db.close()


@click.command()
def get_new_entries():
    db.connect()
    for channel in Subscription.select():
        log.debug(f"Getting data for channel {channel.uuid}")
        for vid, (title, pubdate) in get_channel_entries(channel.uuid).items():
            log.debug(f"{vid}:{pubdate}")
            try:
                Episode.create(uuid=vid, name=title, pub_date=pubdate).save()
                log.debug(f"Entry {vid} added")
            except peewee.IntegrityError:
                log.debug(f"{vid} already in DB, skipping")
        channel.last_check = datetime.now()
        channel.save()
    db.close()


@click.command()
def download():
    db.connect()
    enqueued = EpisodeState.get(EpisodeState.name == "enqueued")
    processed = EpisodeState.get(EpisodeState.name == "processed")
    for ep in Episode.select().where(Episode.state == enqueued):
        log.debug(f"Downloading video {ep}")
        path = download_and_process(ep.uuid)
        log.debug(f"File downloaded: {path}")
        ep.state = processed
        ep.path = path
        ep.save()
    db.close()


@click.command()
def upload():
    db.connect()
    processed = EpisodeState.get(EpisodeState.name == "processed")
    sent = EpisodeState.get(EpisodeState.name == "sent")
    for ep in Episode.select().where(Episode.state == processed):
        log.debug(f'Send {ep.path} to the cloud...')
        mp3 = Path(ep.path)
        if send2bucket(mp3):
            mp3.unlink()
            ep.state = sent
            ep.save()
    db.close()


cli.add_command(sub, name="subscribe")
cli.add_command(list_sub, name="list_subs")
cli.add_command(get_new_entries, name="refresh")
cli.add_command(download, name="download")
cli.add_command(upload, name="upload")


if __name__ == "__main__":
    cli()
