import os
from exif import Image as EXIF
from PIL import Image as ImagePilow
from keras.models import load_model
import shutil
import re
import subprocess
import json
import numpy as np
import tensorflow as tf
import hashlib
import uuid
import pdb

# Supported image file extensions
IMAGE_EXTENSIONS = [
	"jpg", "jpeg", "png", "gif", "svg", "webp"
]

# Supported video file extensions
VIDEO_EXTENSIONS = [
	"mp4", "mkv", "avi", "webm"
]

# Load the trained meme classification model
model = load_model('memeclassifierVersionVideo.keras')

def load_image_for_model(path):
	"""
	Loads and preprocesses an image for the TensorFlow model.

	Steps:
	- Opens the image
	- Converts it to RGB
	- Resizes it to 128x128
	- Normalizes pixel values to range [0, 1]

	Args:
		path (str): Path to the image file.

	Returns:
		np.ndarray | None:
			Preprocessed image array if successful,
			otherwise None if an error occurs.
	"""
	try:
		img = ImagePilow.open(path).convert("RGB")
		img = np.array(img)
		img = tf.image.resize(img, (128, 128))
		img = np.squeeze(img)
		img = img / 255.0

		return img

	except Exception as e:
		print(f"Error con {path}: {e}")
		return None
	

def process_image(path):
	"""
	Process an image file and classify it into categories:
	- Real photo
	- Meme
	- Needs review
	- Corrupted
	- Other

	The function first validates the image, extracts EXIF data,
	and attempts a heuristic classification before using the
	AI meme classifier model.

	Args:
		path (str): Path to the image file.
	"""

	# Skip invalid/corrupted images
	if not is_valid_image_pillow(path):
		return

	exif = get_exif(path)

	# Heuristic classification using EXIF metadata
	classification = classify_image(path, exif)

	# Extract best possible year/date
	date = get_best_date(path, exif)

	# If image appears to be a real photo and has a valid date,
	# organize it directly by year
	if classification == "probablyReal" and date != '0000':
		move_to_folder(path, f'./organized_photos/{date}')
	else:
		# Prepare image for neural network classification
		resized_photo = load_image_for_model(path)

		# Move corrupted images
		if resized_photo is None:
			move_to_folder(path, './organized_photos/corrupted_photos')

		# Ensure image shape is valid
		if len(resized_photo.shape) != 3:
			move_to_folder(path, './organized_photos/corrupted_photos')

		# Predict meme probability
		prediction = model.predict(np.expand_dims(resized_photo, 0))

		# High confidence meme
		if prediction > 0.7:
			move_to_folder(path, './organized_photos/memes')

		# Medium confidence -> manual review
		elif prediction > 0.4:
			move_to_folder(path, './organized_photos/review')

		# Likely a normal image
		else:
			date = get_best_date(path, exif)

			if date == '0000':
				move_to_folder(path, './organized_photos/others')
			else:
				move_to_folder(path, f'./organized_photos/{date}')


def process_video(path):
	"""
	Process a video file and organize it based on metadata.

	If the video appears to come from a real device/camera,
	it is organized by creation year.
	Otherwise, it is moved to the 'others' folder.

	Args:
		path (str): Path to the video file.
	"""
	metadata = get_video_metadata(path)

	if is_video_from_device(metadata):
		date = get_video_date(metadata)
		move_to_folder(path, f'./organized_videos/{date}')
	else:
		move_to_folder(path, './organized_videos/others')

def get_video_metadata(path):
	"""
	Extract metadata from a video file using ffprobe.

	Args:
		path (str): Path to the video file.

	Returns:
		dict: Parsed metadata in JSON format.
	"""
	cmd = [
		"ffprobe",
		"-v", "quiet",
		"-print_format", "json",
		"-show_format",
		"-show_streams",
		path
	]

	result = subprocess.run(cmd, capture_output=True, text=True)
	return json.loads(result.stdout)

def get_video_date(metadata):
	"""
	Extract the creation year from video metadata.

	Args:
		metadata (dict): Video metadata dictionary.

	Returns:
		str: Creation year or 'unknown' if unavailable.
	"""
	try:
		return metadata["format"]["tags"]["creation_time"][:4]
	except:
		return "unknown"
	
def is_video_from_device(metadata):
	"""
	Determine whether a video likely originated
	from a physical recording device.

	Checks:
	- Presence of creation_time
	- Encoder information

	Args:
		metadata (dict): Video metadata.

	Returns:
		bool: True if likely recorded by a device.
	"""
	tags = metadata.get("format", {}).get("tags", {})

	if "creation_time" in tags:
		return True

	if "encoder" in tags and "Lavf" not in tags["encoder"]:
		return True

	return False

def get_exif(path):
	"""
	Extract EXIF metadata from an image.

	Args:
		path (str): Path to the image file.

	Returns:
		dict | None:
			EXIF metadata if available,
			otherwise None.
	"""
	try:
		return ImagePilow.open(path)._getexif()
	except:
		return None
	
def classify_image(path, exif):
	"""
	Heuristically classify an image as:
	- probablyReal
	- probablyMeme

	Scoring is based on:
	- Camera metadata
	- Original timestamp
	- Exposure/lens settings
	- Typical camera filename patterns

	Args:
		path (str): Image file path.
		exif (dict): EXIF metadata.

	Returns:
		str: Classification result.
	"""
	if not exif:
		return "probablyMeme"

	score = 0

	# Camera make/model
	if any(tag in exif for tag in [271, 272]):
		score += 1

	# Original capture date
	if 36867 in exif:  # DateTimeOriginal
		score += 1

	# Camera settings metadata
	if any(tag in exif for tag in [33434, 33437, 34855]):
		score += 1

	# Common camera filename patterns
	filename = os.path.basename(path).lower()
	if "img_" in filename or "dsc_" in filename:
		score += 1

	if score >= 3:
		return "probablyReal"
	else:
		return "probablyMeme"

def get_best_date(path, exif):
	"""
	Extract the best possible year for an image.

	Priority:
	1. EXIF metadata
	2. Filename regex
	3. Default fallback

	Args:
		path (str): Image file path.
		exif (dict): EXIF metadata.

	Returns:
		str: Year string or '0000' if unknown.
	"""

	# 1. EXIF metadata
	if exif and 36867 in exif:
		return str(exif[36867])[:4]

	# 2. Extract year from filename
	filename = os.path.basename(path)
	regex_date = regex_get_date_on_name(filename)
	if regex_date:
		return regex_date

	# 3. Default
	return "0000"

def move_to_folder(path, destination):
	"""
	Move a file into a destination folder.

	If the folder does not exist, it is created automatically.

	Args:
		path (str): Original file path.
		destination (str): Destination directory.
	"""
	if not os.path.exists(destination):
		os.makedirs(destination)

	filename = os.path.basename(path)
	shutil.move(path, os.path.join(destination, filename))

def regex_get_date_on_name(file_name):
	"""
	Extract a year from a filename using regex.

	Matches years between:
	- 1900-1999
	- 2000-2099

	Args:
		file_name (str): File name.

	Returns:
		str | None: Detected year or None.
	"""
	regex = r'(19\d{2}|20\d{2})'
	match = re.search(regex, file_name)

	if match:
		return match.group(1)
	return None

def is_valid_image_pillow(file_name):
	"""
	Validate whether an image can be opened correctly.

	Uses Pillow's verify() method to detect corruption.

	Args:
		file_name (str): Path to image file.

	Returns:
		bool: True if image is valid.
	"""
	try:
		with ImagePilow.open(file_name) as img:
			img.verify()
			return True
	except (IOError, SyntaxError):
		return False
	

def get_file_hash(path):
	"""
	Generate an MD5 hash for a file.

	Used for duplicate detection.

	Args:
		path (str): File path.

	Returns:
		str: MD5 hash string.
	"""

	hasher = hashlib.md5()
	with open(path, 'rb') as f:
		while chunk := f.read(8192):
			hasher.update(chunk)
	return hasher.hexdigest()

# Root directory containing files to organize
root_directory = "./photos"

# Create duplicates folder if it doesn't exist
os.makedirs('./duplicates', exist_ok=True)

# Dictionary used to track file hashes
hashes = {}

# Walk through all files recursively
for dirpath, dirnames, filenames in os.walk(root_directory):
	for file in filenames:
		full_file_path = os.path.join(dirpath, file)

		try:
			file_extension = file.split(".", 1)[-1].lower()

			# Detect duplicate files using MD5 hash
			file_hash = get_file_hash(full_file_path)
			if file_extension in IMAGE_EXTENSIONS:

				# Duplicate detected
				if file_hash in hashes:
					filename = os.path.basename(full_file_path)

					# Rename duplicate to avoid conflicts
					new_name = f"{uuid.uuid4()}_{filename}"
					shutil.move(full_file_path, os.path.join('./duplicates', new_name))
					continue
				else:
					hashes[file_hash] = full_file_path

				# Process image
				process_image(full_file_path)

			elif file_extension in VIDEO_EXTENSIONS:
				# Process video
				process_video(full_file_path)
				pass

			else:
				# Unknown file type
				move_to_folder(full_file_path, './organized_photos/unknown')

		except Exception as e:
			print(f"Error: {full_file_path}: {e}")

