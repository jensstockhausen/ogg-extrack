import csv
import pathlib

import taglib
import click
import pymysql
import pymysql.cursors
from tqdm import tqdm

CSV_FIELDS = ["file", "title", "artist", "album", "duration_seconds", "sample_rate_hz", "bitrate_kbps"]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ogg_tracks (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    file        TEXT         NOT NULL,
    title       VARCHAR(512),
    artist      VARCHAR(512),
    album       VARCHAR(512),
    duration_seconds DECIMAL(10,2),
    sample_rate_hz   INT UNSIGNED,
    bitrate_kbps     SMALLINT UNSIGNED,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

INSERT_SQL = """
INSERT INTO ogg_tracks (file, title, artist, album, duration_seconds, sample_rate_hz, bitrate_kbps)
VALUES (%(file)s, %(title)s, %(artist)s, %(album)s, %(duration_seconds)s, %(sample_rate_hz)s, %(bitrate_kbps)s)
ON DUPLICATE KEY UPDATE
    title=VALUES(title), artist=VALUES(artist), album=VALUES(album),
    duration_seconds=VALUES(duration_seconds), sample_rate_hz=VALUES(sample_rate_hz),
    bitrate_kbps=VALUES(bitrate_kbps)
"""


def open_db(host, port, user, password, database):
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
    )
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def flush_batch(conn, batch):
    if not batch:
        return
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL, batch)
    conn.commit()
    batch.clear()


def interpret_ogg(file_path, quiet=False):
    try:
        audio = taglib.File(str(file_path))

        title = audio.tags.get("TITLE", ["Unknown Title"])[0]
        artist = audio.tags.get("ARTIST", ["Unknown Artist"])[0]
        album = audio.tags.get("ALBUM", ["Unknown Album"])[0]

        length_in_seconds = audio.length
        sample_rate = audio.sampleRate
        bitrate = audio.bitrate
        audio.close()

        if not quiet:
            print(f"File:        {file_path}")
            print(f"--- Metadata ---")
            print(f"Title:  {title}")
            print(f"Artist: {artist}")
            print(f"Album:  {album}")
            print(f"\n--- Technical Info ---")
            print(f"Duration:    {length_in_seconds:.2f} seconds")
            print(f"Sample Rate: {sample_rate} Hz")
            print(f"Bitrate:     {bitrate:.0f} kbps")
            print()

        return {
            "file": str(file_path),
            "title": title,
            "artist": artist,
            "album": album,
            "duration_seconds": f"{length_in_seconds:.2f}",
            "sample_rate_hz": sample_rate,
            "bitrate_kbps": f"{bitrate:.0f}",
        }

    except Exception as e:
        click.echo(f"Error reading {file_path}: {e}", err=True)
        return None


@click.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=pathlib.Path),
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=pathlib.Path),
    default=None,
    help="Write results to a CSV file at this path.",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    default=False,
    help="Suppress per-file output (recommended for large datasets).",
)
@click.option("--db-host", default=None, help="MariaDB host.")
@click.option("--db-port", default=3306, show_default=True, help="MariaDB port.")
@click.option("--db-user", default=None, help="MariaDB user.")
@click.option("--db-password", default=None, help="MariaDB password.", hide_input=True)
@click.option("--db-name", default=None, help="MariaDB database name.")
@click.option("--db-batch-size", default=500, show_default=True, help="Rows per DB batch insert.")
def main(path, output, quiet, db_host, db_port, db_user, db_password, db_name, db_batch_size):
    """Extract metadata from OGG Vorbis files.

    PATH can be a single .ogg file or a directory that will be searched
    recursively for all .ogg files.
    """
    db_enabled = all([db_host, db_user, db_name])
    if any([db_host, db_user, db_name]) and not db_enabled:
        raise click.UsageError("--db-host, --db-user, and --db-name are all required for database output.")

    # Use the generator directly — never materialise the full file list in memory.
    files = iter([path]) if path.is_file() else path.rglob("*.ogg")

    csv_writer = None
    csv_fh = None
    db_conn = None
    db_batch = []
    count = 0

    try:
        if output:
            csv_fh = output.open("w", newline="", encoding="utf-8")
            csv_writer = csv.DictWriter(csv_fh, fieldnames=CSV_FIELDS)
            csv_writer.writeheader()

        if db_enabled:
            db_conn = open_db(db_host, db_port, db_user, db_password or "", db_name)

        with tqdm(files, unit="file", desc="Processing", disable=not quiet) as progress:
            for f in progress:
                progress.set_postfix_str(f.name, refresh=False)
                result = interpret_ogg(f, quiet=quiet)
                if result is None:
                    continue
                count += 1
                if csv_writer:
                    csv_writer.writerow(result)
                if db_conn:
                    db_batch.append(result)
                    if len(db_batch) >= db_batch_size:
                        flush_batch(db_conn, db_batch)

        if db_conn:
            flush_batch(db_conn, db_batch)  # flush remaining rows

    except Exception:
        if db_conn and db_batch:
            db_conn.rollback()  # discard any unflushed partial batch
        raise
    finally:
        if csv_fh:
            csv_fh.close()
        if db_conn:
            db_conn.close()

    if count == 0:
        click.echo("No .ogg files found.", err=True)
        raise SystemExit(1)

    if output:
        click.echo(f"Results written to {output} ({count} files)")
    if db_enabled:
        click.echo(f"Inserted {count} rows into {db_name}.ogg_tracks")


if __name__ == "__main__":
    main()