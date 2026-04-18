import csv
import pathlib

import click
from mutagen.oggvorbis import OggVorbis

CSV_FIELDS = ["file", "title", "artist", "album", "duration_seconds", "sample_rate_hz", "bitrate_kbps"]


def interpret_ogg(file_path):
    try:
        audio = OggVorbis(file_path)

        title = audio.get("title", ["Unknown Title"])[0]
        artist = audio.get("artist", ["Unknown Artist"])[0]
        album = audio.get("album", ["Unknown Album"])[0]

        length_in_seconds = audio.info.length
        sample_rate = audio.info.sample_rate
        bitrate = audio.info.bitrate / 1000

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
def main(path, output):
    """Extract metadata from OGG Vorbis files.

    PATH can be a single .ogg file or a directory that will be searched
    recursively for all .ogg files.
    """
    if path.is_file():
        files = [path]
    else:
        files = sorted(path.rglob("*.ogg"))

    if not files:
        click.echo("No .ogg files found.", err=True)
        raise SystemExit(1)

    rows = [result for f in files if (result := interpret_ogg(f)) is not None]

    if output and rows:
        with output.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        click.echo(f"Results written to {output}")


if __name__ == "__main__":
    main()