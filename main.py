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
import platform
import pdb
import ffmpeg
from datetime import datetime
# from PIL import Image



IMAGE_EXTENSIONS = [
	"jpg", "jpeg", "png", "gif", "svg", "webp"
]

VIDEO_EXTENSIONS = [
	"mp4", "mkv", "avi", "webm"
]

model = load_model('memeclassifier.keras')

def load_image_for_model(path):
	# try:
	#     # 🔍 Validar con PIL primero
	#     with ImagePilow.open(path) as img:
	#         img.verify()

	#     img = tf.io.read_file(path)
	#     img = tf.image.decode_image(img, channels=3)
	#     img = tf.image.resize(img, (256, 256))
	#     img = img / 255.0

	#     return img

	# except Exception as e:
	#     print(f"Imagen inválida: {path} → {e}")
	#     return None
	try:

		img = ImagePilow.open(path).convert("RGB")
		img = np.array(img)
		img = tf.image.resize(img, (256, 256))
		img = np.squeeze(img)
		img = img / 255.0

		return img

	except Exception as e:
		print(f"Error con {path}: {e}")
		return None
	

# Divifir este metodo para que use la prediccion aparte
def process_image(path):
	if not is_valid_image_pillow(path):
		return

	exif = get_exif(path)
	classification = classify_image(path, exif)
	date = get_best_date(path, exif)

	print('classification')
	print(classification)

	if classification == "probablyReal" and date != '0000':
		move_to_folder(path, f'./organized_photos/{date}')
	else:
		resized_photo = load_image_for_model(path)

		if resized_photo is None:
			move_to_folder(path, './organized_photos/corrupted_photos')

		if len(resized_photo.shape) != 3:
			move_to_folder(path, './organized_photos/corrupted_photos')

		prediction = model.predict(np.expand_dims(resized_photo, 0))

		if prediction < 0.3:
			print(f'el archivo {path} es un meme')
			move_to_folder(path, './organized_photos/memes')
		else:
			#Here we are sure that is not a meme, so we try to classified
			date = get_best_date(path, exif)
			if date == '0000':
				move_to_folder(path, './organized_photos/others')
			else:
				move_to_folder(path, f'./organized_photos/{date}')


def process_video(path):
	date = get_best_date_video(path)
	is_probably_from_camera = is_probably_camera_video(path)

	print(f"is_probably_from_camera{path}")
	print(is_probably_from_camera)

	if date != '0000' and is_probably_from_camera:
		move_to_folder(path, f'./organized_videos/{date}')
		pass
	# print("date")
	# print(date)
	
	# if is_video_from_device(metadata):
	# 	date = get_video_date(metadata)
	# 	move_to_folder(path, f'./organized_videos/{date}')
	# else:
	# 	move_to_folder(path, './organized_videos/others')

# def get_video_metadata_linux(path):
# 	cmd = ["ffprobe","-v", "quiet","-print_format", "json","-show_format","-show_streams",path]
# 	result = subprocess.run(cmd, capture_output=True, text=True)
# 	return json.loads(result.stdout)

# def get_video_metadata_windows(path):
# 	properties = propsys.SHGetPropertyStoreFromParsingName(path)
# 	dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
# 	return dt

def get_best_date_video(path):
	probe = ffmpeg.probe(path)

	# 🔹 1. Buscar en format
	format_tags = probe.get('format', {}).get('tags', {})
	creation_time = format_tags.get('creation_time')

	if creation_time:
		dt = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%S.%fZ")
		year = str(dt.year)
		return year

	streams = probe.get('streams', [])
	for stream in streams:
		tags = stream.get('tags', {})
		if 'creation_time' in tags:
			creation_time = tags['creation_time']
			dt = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%S.%fZ")
			year = str(dt.year)
			return year

	# 2. Nombre
	filename = os.path.basename(path)
	regex_date = regex_get_date_on_name(filename)
	if regex_date:
		return regex_date

	return "0000"

def is_probably_camera_video(path):
	probe = ffmpeg.probe(path)

	tags = probe.get('format', {}).get('tags', {})

	# 🔹 Señales de cámara
	if any(k.startswith('com.android') for k in tags):
		return True

	if any(k.startswith('com.apple') for k in tags):
		return True

	# 🔹 Nombre tipo cámara (YYYYMMDD_HHMMSS)
	import re
	if re.search(r'\d{8}_\d{6}', path):
		return True

	return False

def get_video_date(metadata):
	try:
		return metadata["format"]["tags"]["creation_time"][:4]
	except:
		return "unknown"
	
def is_video_from_device(metadata):
	tags = metadata.get("format", {}).get("tags", {})

	if "creation_time" in tags:
		return True

	if "encoder" in tags and "Lavf" not in tags["encoder"]:
		return True

	return False

def get_exif(path):
	try:
		return ImagePilow.open(path)._getexif()
	except:
		return None
	
def classify_image(path, exif):
	if not exif:
		return "probablyMeme"

	score = 0

	# Cámara
	if any(tag in exif for tag in [271, 272]):  # Make, Model
		score += 1

	if 36867 in exif:  # DateTimeOriginal
		score += 1

	# Parámetros técnicos
	if any(tag in exif for tag in [33434, 33437, 34855]):
		score += 1

	# Nombre del archivo (heurística)
	filename = os.path.basename(path).lower()
	if "img_" in filename or "dsc_" in filename:
		score += 1

	if score >= 3:
		return "probablyReal"
	else:
		return "probablyMeme"

def get_best_date(path, exif):
	# 1. EXIF
	if exif and 36867 in exif:
		return str(exif[36867])[:4]

	# 2. Nombre
	filename = os.path.basename(path)
	regex_date = regex_get_date_on_name(filename)
	if regex_date:
		return regex_date

	# 3. Default
	return "0000"

def move_to_folder(path, destination):
	if not os.path.exists(destination):
		os.makedirs(destination)

	filename = os.path.basename(path)
	shutil.move(path, os.path.join(destination, filename))

def regex_get_date_on_name(file_name):
	regex = r'(19\d{2}|20\d{2})'
	match = re.search(regex, file_name)

	if match:
		return match.group(1)
	return None

def is_valid_image_pillow(file_name):
	try:
		with ImagePilow.open(file_name) as img:
			img.verify()
			return True
	except (IOError, SyntaxError):
		return False
	

def get_file_hash(path):
	hasher = hashlib.md5()
	with open(path, 'rb') as f:
		while chunk := f.read(8192):
			hasher.update(chunk)
	return hasher.hexdigest()

root_directory = "./photos"
os.makedirs('./duplicates', exist_ok=True)
hashes = {}

for dirpath, dirnames, filenames in os.walk(root_directory):
	for file in filenames:
		# pdb.set_trace()
		full_file_path = os.path.join(dirpath, file)

		try:
			file_extension = file.split(".", 1)[-1].lower()

			file_hash = get_file_hash(full_file_path)
			if file_extension in IMAGE_EXTENSIONS:


				if file_hash in hashes:
					# duplicado exacto
					filename = os.path.basename(full_file_path)
					new_name = f"{uuid.uuid4()}_{filename}"
					destination = os.path.join('./duplicates', new_name)
					shutil.move(full_file_path, destination)
					print(f"Duplicado movido: {full_file_path}")
					continue

			else:
				hashes[file_hash] = full_file_path

			if file_extension in IMAGE_EXTENSIONS:
				process_image(full_file_path)

			elif file_extension in VIDEO_EXTENSIONS:
				# pass
				process_video(full_file_path)

			else:
				move_to_folder(full_file_path, f'./organized_photos/unknown')

		except Exception as e:
			print(f"Error con {full_file_path}: {e}")

