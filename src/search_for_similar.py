"""
Based on https://mathspp.com/blog/finding-similar-photos
"""
import os
import pprint
from datetime import timedelta
from itertools import product
from pathlib import Path
from timeit import default_timer as timer
import json
import PIL
from PIL import Image, ImageChops


def summarise(img: Image.Image) -> Image.Image:
    """Summarise an image into a 16 x 16 image."""
    resized = img.resize((16, 16))
    return resized


def difference(img1: Image.Image, img2: Image.Image) -> float:
    """Find the difference between two images."""
    diff = ImageChops.difference(img1, img2)

    acc = 0
    width, height = diff.size
    for w, h in product(range(width), range(height)):
        r, g, b = diff.getpixel((w, h))
        acc += (r + g + b) / 3

    average_diff = acc / (width * height)
    normalised_diff = average_diff / 255
    return normalised_diff


def process_images(directory, target_image_summary: Image.Image, threshold=0.07) -> [str]:
    count = 0
    failures:[str]=[]
    # Traverse the directory recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            count += 1

            # Check if the file is a JPEG or PNG image
            if file.lower().endswith(('.jpeg', '.jpg'))\
                    and not file.startswith('.'):
                # Get the full path of the image file
                candidate_filepath = os.path.join(root, file)
                candidate: Image.Image  # declare for hinting
                try:
                    with (Image.open(candidate_filepath)) as candidate:
                        candidate_summary = summarise(candidate)

                        diff = difference(target_image_summary, candidate_summary)
                        if diff < threshold:
                            print(f'open "{candidate_filepath}" | diff {diff:0.2f}')
                except ValueError as ex:
                    # see: https://stackoverflow.com/questions/12291641/python-pil-valueerror-images-do-not-match
                    msg = f"diff failed: \"{candidate_filepath}\""
                    print(msg)
                except PIL.Image.DecompressionBombError as ddos_ex:
                    msg = f"too big    : \"{candidate_filepath}\""
                    print(msg)
                except OSError as ex:
                    failures.append(f"\"{candidate_filepath}\"")
                    # print(f"failed to process \"{candidate_filepath}\" - {ex}")

    print(f"Processed {count} files; there were {len(failures)} failures")
    return failures


if __name__ == "__main__":
    becky_at_work_2018_img = Path("/Users/becky/Library/CloudStorage/Dropbox/Pictures/2018/20180105 09.40.28.jpg")
    pictures_2018_dir = Path("/Users/becky/Library/CloudStorage/Dropbox/Pictures/2018")

    parked_img = Path('/Users/becky/Library/CloudStorage/Dropbox/Pictures/TestDupes/G0011347.JPG')
    test_dupes_dir = Path('/Users/becky/Library/CloudStorage/Dropbox/Pictures/TestDupes/')

    fire_escape_photos_file_path = Path(
        "/Users/becky/Library/CloudStorage/Dropbox/Pictures/NY Alley at Night from Imgur.jpeg")
    pictures_dir = Path("/Users/becky/Library/CloudStorage/Dropbox/Pictures")
    camera_upload_dir = Path("/Users/becky/Library/CloudStorage/Dropbox/Camera Uploads")

    # configure
    matching_threshold = 0.06
    subject_image_path = fire_escape_photos_file_path
    target_dir_path = pictures_dir
    print(f"Looking for images similar to {subject_image_path} in {target_dir_path}")

    # im : Image.Image = Image.open(subject_image_path)
    im: Image.Image  # declare for hinting
    with (Image.open(subject_image_path)) as im:
        subject_summary = summarise(im)

    start = timer()
    fails : [str] = process_images(target_dir_path, target_image_summary=subject_summary, threshold=matching_threshold)
    end = timer()
    delta = timedelta(seconds=end - start)
    print(f"\nexecution duration: {delta}")

    print(f"\n\n\n# list of all {len(fails)} failures:")
    json_data = json.dumps(fails, indent=4)

    # Printing the result
    print(pprint.pformat(json_data, indent=4,width=120))

    # Writing the result to a file
    with open('fails.json', 'w') as file:
        file.write(json_data)
    print("###")
