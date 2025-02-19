from pathlib import Path
from util.exif_date import ExifDate


class ExifSidecar(ExifDate):
    def __init__(self, file_path, dry_run=False):
        super().__init__(file_path, dry_run)

    def get_corresponding_image_file(self):
        image_extensions = self.EXTENSIONS

        for ext in image_extensions:
            image_file = self.file_path.with_suffix(ext)
            if image_file.exists():
                return image_file

        base_name = self.file_path.stem
        for ext in image_extensions:
            image_file = self.file_path.with_name(base_name + ext)
            if image_file.exists():
                return image_file

        for ext in image_extensions:
            for file in self.file_path.parent.glob(f"{base_name}*"):
                if file.suffix.lower() == ext:
                    return file

        print(f"No image found for sidecar: {self.file_path}")
        return None

    def process(self):
        metadata_date = self.extract_metadata_date()

        if not metadata_date:
            corresponding_image_file = self.get_corresponding_image_file()
            if corresponding_image_file:
                extractor = ExifDate(corresponding_image_file, dry_run=self.dry_run)
                metadata_date = extractor.extract_metadata_date()
                if not metadata_date:
                    metadata_date = extractor.extract_modification_date()

        if metadata_date:
            self.apply_date(metadata_date)
