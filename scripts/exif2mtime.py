#!/usr/bin/env python
import os
from pathlib import Path
from datetime import datetime
import argparse
from util.exif_date import ExifDate
from util.exif_sidecar import ExifSidecar

ALLOWED_EXTENSIONS = set(ExifDate.EXTENSIONS)


def process(args, path=None):
    if path is None:
        path = Path(".")

    files = []

    current_year = datetime.now().year

    if path.is_dir():
        search_method = path.rglob if args.recurse else path.glob
        for file in search_method("*"):
            if file.is_file() and file.suffix.lower() in ALLOWED_EXTENSIONS:
                if (
                    args.any_date
                    or datetime.fromtimestamp(file.stat().st_mtime).year == current_year
                ):
                    files.append(file)
    elif path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
        if (
            args.any_date
            or datetime.fromtimestamp(path.stat().st_mtime).year == current_year
        ):
            files.append(path)

    for file in files:
        process_file(file, args.dry_run, args.timezone)


def process_file(file_path, dry_run, timezone_str=None):
    print(f"Processing file: {file_path}")

    if file_path.suffix.lower() not in [".xmp", ".xcf"]:
        extractor = ExifDate(file_path, dry_run=dry_run, timezone_str=timezone_str)
    else:
        extractor = ExifSidecar(file_path, dry_run=dry_run)

    metadata_date = extractor.extract_metadata_date()
    if not metadata_date:
        print(f"No EXIF date found in file {file_path}")
        return

    try:
        if metadata_date:
            extractor.apply_date(metadata_date)
    except ValueError as e:
        print(f"Error processing file {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Set file ctime and mtime from metadata."
    )
    parser.add_argument(
        "file_specifier", nargs="*", help="Files or directories to process"
    )
    parser.add_argument(
        "-r", "--recurse", action="store_true", help="Recursively process directories"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Dry run (display dates without applying)",
    )
    parser.add_argument(
        "-a",
        "--any-date",
        action="store_true",
        help="Process files with any mtime (default is to only process files with mtime in the current year)",
    )
    parser.add_argument(
        "-t",
        "--timezone",
        help="Timezone to use for date conversion (default is local system timezone)",
    )
    args = parser.parse_args()

    if not args.file_specifier:
        process(args)
    else:
        for file_specifier in args.file_specifier:
            process(args, Path(file_specifier))


def maintest():
    class Args:
        def __init__(self):
            self.file_specifier = ["./testfiles/"]
            self.recurse = True
            self.dry_run = True
            self.any_date = True
            self.timezone = None

    args = Args()
    process(args)


if __name__ == "__main__":
    if os.getenv("TEST_MODE") == "1":
        maintest()
    else:
        main()
