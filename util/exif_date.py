import os
from pathlib import Path
from datetime import datetime
import exiftool
from dateutil import parser
import pytz
from tzlocal import get_localzone


class ExifDate:
    DATE_FIELDS = [
        "MetadataDate",
        "ModifyDate",
        "CreateDate",
        "DateCreated",
        "DateTimeCreated",
        "DateTime",
        "DateTimeOriginal",
        "GPSDateStamp",
        "GPSDateTime",
        "DateTimeDigitized",
        "SubSecCreateDate",
        "SubSecDateTimeOriginal",
        "SubSecModifyDate",
    ]

    EXTENSIONS = [
        ".3gp",
        ".avi",
        ".cr2",
        ".exr",
        ".gif",
        ".jpeg",
        ".jpg",
        ".mov",
        ".mp4",
        ".png",
        ".tif",
        ".xcf",
        ".xmp",
    ]

    def __init__(self, file_path, dry_run=False, timezone_str=None):
        self.file_path = Path(file_path)
        self.dry_run = dry_run
        self.timezone_str = timezone_str or str(get_localzone())

    def extract_metadata_date(self):
        try:
            with exiftool.ExifToolHelper() as et:
                metadata = et.get_metadata(str(self.file_path))

            if isinstance(metadata, list):
                if len(metadata) > 1:
                    print(
                        f"Warning: Multiple metadata dictionaries found for file {self.file_path}"
                    )
                metadata = metadata[0]

            date_fields = {}
            first_date_field = None
            current_year = datetime.now().year

            # Collect all "date" fields into a dictionary and remember the first one
            for key, value in metadata.items():
                if "file" in key.lower():
                    continue
                if "date" in key.lower():
                    if first_date_field is None:
                        first_date_field = (key, value)
                    date_fields[key] = value

            selected_date_field = None

            # Look for all DATE_FIELDS in order in the dictionary
            for field in self.DATE_FIELDS:
                for key, value in date_fields.items():
                    if field.lower() in key.lower():
                        selected_date_field = (key, value)
                        break
                if selected_date_field:
                    break

            # If no DATE_FIELDS are found, use the first date field
            if not selected_date_field and first_date_field:
                selected_date_field = first_date_field

            # Parse the selected date field
            if selected_date_field:
                key, value = selected_date_field
                try:
                    parsed_date = self.parse_date(value)
                    local_date = parsed_date.astimezone(
                        pytz.timezone(self.timezone_str)
                    )
                    found_date = local_date.strftime("%Y%m%d%H%M%S%z")
                    if found_date.startswith(str(current_year)):
                        print(
                            f"Warning: Found a date in {current_year} for file {self.file_path}"
                        )
                    self.log_new_tags(metadata)
                    return found_date
                except ValueError:
                    print(f"Invalid date format. {self.file_path}:  {key} --- {value}")

            self.log_new_tags(metadata)
            return None
        except Exception as e:
            print(f"Error extracting metadata date for file {self.file_path}: {e}")
            return None

    def parse_date(self, date_str):
        try:
            # Check for specific known formats first
            if ":" in date_str and len(date_str.split(":")[0]) == 4:
                # Likely a date in the format "YYYY:MM:DD HH:MM:SS" or "YYYY:MM:DD HH:MM"
                try:
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S%z")
                except ValueError:
                    # Handle case where seconds are missing
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M%z")

            # Try parsing with dateutil.parser
            parsed_date = parser.parse(date_str)

            # Check if the parsed date is within a reasonable range
            if not (1900 <= parsed_date.year <= datetime.now().year):
                raise ValueError(f"Parsed date {parsed_date} is out of range.")

            return parsed_date
        except ValueError:
            # Try common date formats manually
            date_formats = [
                "%Y:%m:%d %H:%M:%S%z",
                "%Y:%m:%d %H:%M%z",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%d %H:%M%z",
                "%Y/%m/%d %H:%M:%S%z",
                "%Y/%m/%d %H:%M%z",
                "%Y%m%d %H:%M:%S%z",
                "%Y%m%d %H:%M%z",
                "%Y%m%dT%H%M%S%z",
                "%Y%m%dT%H%M%z",
            ]
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)

                    # Check if the parsed date is within a reasonable range
                    if not (1900 <= parsed_date.year <= datetime.now().year):
                        raise ValueError(f"Parsed date {parsed_date} is out of range.")

                    return parsed_date
                except ValueError:
                    continue
            raise ValueError(f"Date format not recognized: {date_str}")

    def log_new_tags(self, metadata):
        with open("newtags.txt", "a") as log_file:
            for key, value in metadata.items():
                if "FILE:" in key.upper():
                    continue
                # Remove prefix and check if the tag is new
                tag_name = key.split(":")[-1]
                if "Date" in tag_name and tag_name not in self.DATE_FIELDS:
                    log_file.write(f"{tag_name}: {value}\n")

    def apply_date(self, datetime_str):
        try:
            # Parse the datetime string with timezone information
            parsed_datetime = parser.parse(datetime_str)

            # Convert to local time zone if it's in UTC
            if parsed_datetime.tzinfo is not None:
                local_datetime = parsed_datetime.astimezone(
                    pytz.timezone(self.timezone_str)
                )
            else:
                local_datetime = parsed_datetime

            old_date = datetime.fromtimestamp(self.file_path.stat().st_mtime).strftime(
                "%Y%m%d"
            )
            new_date = local_datetime.strftime("%Y%m%d")
            if self.dry_run:
                print(f"Dry run: {self.file_path} {old_date} -> {new_date}")
            else:
                os.utime(
                    self.file_path,
                    (local_datetime.timestamp(), local_datetime.timestamp()),
                )
        except Exception as e:
            print(f"Error applying date for file {self.file_path}: {e}")
