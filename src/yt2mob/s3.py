from pathlib import Path

import yaml
from cloudpathlib import CloudPath, S3Client
from loguru import logger as log

S3_CFG_FILE = Path(__file__).parent / "s3.yml"


def read_s3_config(cfg_file_path: Path = S3_CFG_FILE) -> dict:
    try:
        with cfg_file_path.open("r", encoding="utf-8") as cfg_file:
            return yaml.load(cfg_file.read(), yaml.Loader)
    except IOError:
        return {}


s3cfg = read_s3_config()
s3client = S3Client(
    aws_access_key_id=s3cfg["access_key"],
    aws_secret_access_key=s3cfg["secret_key"],
    endpoint_url=s3cfg["endpoint"],
)

bucket = CloudPath(f"s3://{s3cfg['bucket']}/", client=s3client)


def send2bucket(path: Path) -> bool:
    log.debug(f"Sending file {path} to bucket...")
    newfile = bucket / path.name.replace(' ','_')
    try:
        newfile.upload_from(path)
        log.debug(f"File {path} sent")
        return True
    except:
        return False