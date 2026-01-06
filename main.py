import os
from exif import Image as EXIF
from PIL import Image as ImagePilow
import shutil
import re

IMAGE_EXTENSIONS = [
    "jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif",
    "svg", "ico", "heic", "heif", "xcf",
    "raw", "cr2", "nef", "arw", "dng", "orf", "rw2"
]

VIDEO_EXTENSIONS = [
    "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm",
    "mpeg", "mpg", "m4v", "3gp", "mts", "m2ts", "vob", "ogv"
]

# with open('./photos/Fotos DropBox/20.jpg', 'rb') as image_file:
    #  my_image = Image(image_file)

# print(my_image.has_exif)
# print(my_image.list_all())
# print(my_image.datetime_original)

def regex_get_date_on_name(file_name):
    print(f'entre para {file_name}')
    regex = r'\b(?:19\d{2}|2\d{3})\b'
    date = re.search(regex, file_name)
    print('date')
    print(date)

    if date:
        print('date.group()')  # 2014
        print(date.group())  # 2014
        return date.group()
    else:
        return None


def is_valid_image_pillow(file_name):
    try:
        with ImagePilow.open(file_name) as img:
            img.verify()
            return True
    except (IOError, SyntaxError):
        return False
    
def get_format(file_name):
    img = ImagePilow.open(file_name)
    # print("Format")
    # print(img.format)
    return str(img.format)
    
def get_date_taken(path):
    exif = ImagePilow.open(path)._getexif()
    if exif is None:
        return '0000'
        
    if 36867 in exif:
        date = exif[36867]
    else:
        date = '0000'

    return str(date)[0:4]

root_directory = "./photos"
print(f"Walking through directory: {root_directory}")
for dirpath, dirnames, filenames in os.walk(root_directory):
    print(f"\nCurrently in directory: {dirpath}")
    # if dirnames:
        # print(f"Subdirectories found: {dirnames}")
    if filenames:
        # print(f"Files found: {filenames}")
        for file in filenames:
            # print(f"file_name: {file}")
            # Construct the full file path using os.path.join
            full_file_path = os.path.join(dirpath, file)
            with open(full_file_path, 'rb') as image_file:
                file_extension = file.split(".",1)[1]
                if file_extension in IMAGE_EXTENSIONS:

                    if is_valid_image_pillow(full_file_path):
                        print("full_file_path")
                        print(full_file_path)
                        print(get_date_taken(full_file_path))
                        date = get_date_taken(full_file_path)
                        if date == '0000':
                            regex_date = regex_get_date_on_name(file)
                            if regex_date is not None:
                                date = regex_date

                        newpath = r'./orginzed_photos/'+date 
                        if not os.path.exists(newpath):
                            os.makedirs(newpath)

                        shutil.move(full_file_path,(newpath+'/'+file))


                        # format_image_file = get_format(image_file)

                        # if format_image_file == 'JPEG' or format_image_file == 'JPG':
                        #     my_image = EXIF(image_file)
                        #     print('my_image')
                        #     print(my_image.list_all())
                        #     # print(my_image.has_exif)
                        
                        #     if my_image.has_exif:
                        #         print('my_image')
                        #         print(my_image)
                        
                        # elif format_image_file == "PNG":
                        #     print("entre al PNG")
                        #     img = ImagePilow.open(image_file)
                        #     print('img.info')
                        #     print(img.info)
                        #     print(type(img.info))
                        #     print(img.info['CreateDate'])

                elif file_extension in VIDEO_EXTENSIONS:
                    print('still working on this')


