import csv
import pathlib

import click
from mutagen.oggvorbis import OggVorbis
from tqdm import tqdm

CSV_FIELDS = ["file", "title", "artist", "album", "duration_seconds", "sample_rate_hz", "bitrate_kbps"]


def interpret_ogg(file_path, quiet=False):
    try:
        audio = OggVorbis(file_path)

        title = audio.get("title", ["Unknown Title"])[0]
        artist = audio.get("artist", ["Unknown Artist"])[0]
        album = audio.get("album", ["Unknown Album"])[0]

        length_in_seconds = audio.info.length
        sample_rate = audio.info.sample_rate
        bitrate = audio.info.bitrate / 1000

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
def main(path, output, quiet):
    """Extract metadata from OGG Vorbis files.

    PATH can be a single .ogg file or a directory that will be searched
    recursively for all .ogg files.
    """
    # Use the generator directly — never materialise the full file list in memory.
    files = iter([path]) if path.is_file() else path.rglob("*.ogg")

    csv_writer = None
    csv_fh = None
    count = 0

    try:
        if output:
            csv_fh = output.open("w", newline="", encoding="utf-8")
            csv_writer = csv.DictWriter(csv_fh, fieldnames=CSV_FIELDS)
            csv_writer.writeheader()

        with tqdm(files, unit="file", desc="Processing", disable=not quiet) as progress:
            for f in progress:
                progress.set_postfix_str(f.name, refresh=False)
                result = interpret_ogg(f, quiet=quiet)
                if result is None:
                    continue
                count += 1
                if csv_writer:
                    csv_writer.writerow(result)
    finally:
        if csv_fh:
            csv_fh.close()

    if count == 0:
        click.echo("No .ogg files found.", err=True)
        raise SystemExit(1)

    if output:
        click.echo(f"Results written to {output} ({count} files)")


if __name__ == "__main__":
    main()