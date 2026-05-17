# MediaSieve

AI-powered media organizer that automatically classifies and sorts photos and videos using EXIF metadata, file heuristics, duplicate detection, and a TensorFlow meme classifier.

---

## Features

- 📷 Detects and organizes real photos by year
- 🤖 Uses a TensorFlow/Keras model to classify memes
- 🎥 Organizes videos based on metadata
- 🧠 Uses EXIF data and filename heuristics before AI classification
- 🔍 Detects duplicate files using MD5 hashes
- 🗂 Automatically creates organized folder structures
- ⚠ Separates suspicious or uncertain files into a manual review folder
- 💥 Detects corrupted images
- 📁 Supports recursive folder scanning

---

## How It Works

The program scans every file inside the `./photos` directory and processes them according to their type.

### Image Processing Pipeline

For every image:

1. Validate the image using Pillow
2. Extract EXIF metadata
3. Attempt heuristic classification:
   - Camera model
   - Original capture date
   - Lens/exposure metadata
   - Common camera filename patterns
4. If the image looks like a real photo:
   - Organize it by year
5. Otherwise:
   - Resize image to `128x128`
   - Run TensorFlow meme classifier
   - Classify as:
     - Meme
     - Review
     - Normal photo
     - Corrupted

---

### Video Processing Pipeline

For videos:

1. Extract metadata using `ffprobe`
2. Detect whether the video comes from a real device
3. Extract creation year
4. Organize by year or move to `others`

---

### Duplicate Detection

Before processing any image:

- The file's MD5 hash is calculated
- If another identical file already exists:
  - The duplicate is moved into `./duplicates`
  - A UUID is added to avoid filename conflicts

---

## Supported File Types

### Images

- JPG
- JPEG
- PNG
- GIF
- SVG
- WEBP

### Videos

- MP4
- MKV
- AVI
- WEBM

---

# Technologies Used

- Python
- TensorFlow
- Keras
- Pillow
- EXIF
- NumPy
- FFmpeg / ffprobe

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/MediaSieve.git

cd MediaSieve
```

---

## 2. Create a Virtual Environment

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

---

## 3. Install Python Dependencies

```bash
pip install tensorflow keras pillow exif numpy
```

Or using a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## 4. Install FFmpeg

This project requires `ffprobe` for video metadata extraction.

### Ubuntu / Debian

```bash
sudo apt install ffmpeg
```

### Fedora

```bash
sudo dnf install ffmpeg
```

### Arch Linux

```bash
sudo pacman -S ffmpeg
```

### Windows

Download FFmpeg from:

https://ffmpeg.org/download.html

Then add FFmpeg to your system PATH.

---

# Usage

## 1. Add Your Media

Place all photos and videos inside:

```bash
./photos
```

The script scans folders recursively, so nested folders are supported.

Example:

```bash
photos/
├── phone_backup/
├── memes/
├── whatsapp/
└── random/
```

---

## 2. Run the Script

```bash
python main.py
```

---

# Output Folders

After execution, files will automatically be organized into:

| Folder | Description |
|---|---|
| `organized_photos/YYYY` | Real photos grouped by year |
| `organized_photos/memes` | High-confidence memes |
| `organized_photos/review` | Medium-confidence classifications |
| `organized_photos/others` | Files without valid dates |
| `organized_photos/corrupted_photos` | Invalid or broken images |
| `organized_photos/unknown` | Unsupported file types |
| `organized_videos/YYYY` | Videos grouped by year |
| `organized_videos/others` | Videos without reliable metadata |
| `duplicates` | Duplicate files |

---

# AI Model

The project uses a TensorFlow/Keras binary classification model trained to distinguish:

- Real photos
- Memes

The model file used is:

```bash
memeclassifierVersionVideo.keras
```

---

# Datasets Used

## Selfie and Official ID Dataset

Used as part of the real-photo training data.

Dataset source:

https://huggingface.co/datasets/AxonData/Selfie_and_Official_ID_Photo_Dataset

---

## Meme Dataset

Used to train the meme classification model.

Dataset source:

https://huggingface.co/datasets/kuzheren/100k-random-memes/tree/main

---

# Notes

- EXIF metadata is not always available.
- Some memes may still be classified as normal images.
- Videos generated or edited by software may not contain reliable metadata.
- Large media libraries may require significant processing time.
