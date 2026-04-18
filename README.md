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

**Write results to a MariaDB database:**
```bash
python extract.py path/to/music/ --quiet \
  --db-host localhost \
  --db-user ogg \
  --db-password secret \
  --db-name media
```

The table `ogg_tracks` is created automatically if it does not exist.

**CSV and database simultaneously:**
```bash
python extract.py path/to/music/ --quiet -o results.csv \
  --db-host localhost --db-user ogg --db-password secret --db-name media
```

### Database options

| Option | Default | Description |
|---|---|---|
| `--db-host` | — | MariaDB host (required for DB output) |
| `--db-port` | `3306` | MariaDB port |
| `--db-user` | — | MariaDB user (required for DB output) |
| `--db-password` | — | MariaDB password |
| `--db-name` | — | Database name (required for DB output) |
| `--db-batch-size` | `500` | Rows inserted per batch (tune for performance) |

### Database schema

```sql
CREATE TABLE ogg_tracks (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    file             TEXT NOT NULL,
    title            VARCHAR(512),
    artist           VARCHAR(512),
    album            VARCHAR(512),
    duration_seconds DECIMAL(10,2),
    sample_rate_hz   INT UNSIGNED,
    bitrate_kbps     SMALLINT UNSIGNED,
    imported_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

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

Use `--quiet` / `-q` to suppress per-file output and show a progress bar instead (recommended for large datasets).

## Help

```bash
python extract.py --help
```
