
import subprocess
import json
import logging
import shutil

logger = logging.getLogger(__name__)

def get_exiftool_path():
    """
    Get the path to the exiftool executable.
    Returns 'exiftool' if found in PATH, or checks specific locations.
    """
    if shutil.which("exiftool"):
        return "exiftool"
    # Add other platform-specific checks if necessary
    return None

def extract_metadata(file_path: str) -> dict:
    """
    Extract metadata from a file using ExifTool.
    
    Args:
        file_path (str): The absolute path to the file.
        
    Returns:
        dict: A dictionary containing the extracted metadata. 
              Returns an empty dict if extraction fails.
    """
    exiftool_cmd = get_exiftool_path()
    
    if not exiftool_cmd:
        logger.error("ExifTool not found. Please ensure it is installed and in the PATH.")
        return {}

    try:
        # -j: JSON output
        # -g: Group output by tag group (e.g., EXIF, IPTC, XMP)
        # -struct: Enable structured output for XMP
        # --Binary: Do not extract binary data (too large)
        cmd = [
            exiftool_cmd,
            "-j",
            "-g",
            "-struct",
            "--Binary",
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8' # Ensure UTF-8 encoding
        )
        
        if not result.stdout:
            logger.warning(f"ExifTool returned no output for {file_path}")
            return {}
            
        # ExifTool returns a list of objects (one per file)
        metadata_list = json.loads(result.stdout)
        
        if metadata_list and len(metadata_list) > 0:
            return metadata_list[0]
            
        return {}

    except subprocess.CalledProcessError as e:
        logger.error(f"ExifTool failed with error: {e.stderr}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ExifTool output: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error during metadata extraction: {e}")
        return {}
