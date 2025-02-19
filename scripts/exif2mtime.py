#!/usr/bin/env python
import os
from pathlib import Path
from datetime import datetime
import argparse
from util.exif_date import ExifDate, process_file
from util.exif_sidecar import ExifSidecar

ALLOWED_EXTENSIONS = set(ExifDate.EXTENSIONS)


def process(args):
    files = []

    current_year = datetime.now().year

    if not args.file_specifier:
        path = Path(".")
        search_method = path.rglob if args.recurse else path.glob
        for file in search_method("*"):
            if file.suffix.lower() in ALLOWED_EXTENSIONS:
                if (
                    args.any_date
                    or datetime.fromtimestamp(file.stat().st_mtime).year == current_year
                ):
                    files.append(file)
    else:
        for file_specifier in args.file_specifier:
            path = Path(file_specifier)
            if path.is_dir():
                search_method = path.rglob if args.recurse else path.glob
                for file in search_method("*"):
                    if file.suffix.lower() in ALLOWED_EXTENSIONS:
                        if (
                            args.any_date
                            or datetime.fromtimestamp(file.stat().st_mtime).year
                            == current_year
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

    process(args)


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
