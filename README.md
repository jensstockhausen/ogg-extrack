# ogg-extract

Extract metadata and technical info from OGG Vorbis audio files.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

**Single file:**
```bash
python extract.py path/to/file.ogg
```

**Recursively scan a directory:**
```bash
python extract.py path/to/music/
```

**Write results to a CSV file:**
```bash
python extract.py path/to/music/ --output results.csv
python extract.py track.ogg -o results.csv
```

The CSV contains the columns: `file`, `title`, `artist`, `album`, `duration_seconds`, `sample_rate_hz`, `bitrate_kbps`.

## Output

For each file found, the following is printed:

```
File:        path/to/file.ogg
--- Metadata ---
Title:  Track Title
Artist: Artist Name
Album:  Album Name

--- Technical Info ---
Duration:    213.45 seconds
Sample Rate: 44100 Hz
Bitrate:     192 kbps
```

## Help

```bash
python extract.py --help
```
