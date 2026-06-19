"""
Based on https://mathspp.com/blog/finding-similar-photos
"""

import json
import os
import pprint
from datetime import timedelta
from pathlib import Path
from timeit import default_timer as timer

from PIL import Image, ImageChops

# Prevent decompression bomb DoS attacks on large images
Image.MAX_IMAGE_PIXELS = 10_000 * 10_000


def summarise(img: Image.Image) -> Image.Image:
    """Summarise an image into a 16 x 16 image."""
    # Convert to RGB first to ensure matching modes for ImageChops.difference
    img = img.convert("RGB")
    resized = img.resize((16, 16))
    return resized


def difference(img1: Image.Image, img2: Image.Image) -> float:
    """Find the difference between two images."""
    diff = ImageChops.difference(img1, img2)

    # Use getdata() for a much faster iteration than nested loops + getpixel()
    total = sum((r + g + b) / 3 for r, g, b in diff.getdata())
    num_pixels = diff.width * diff.height
    average_diff = total / num_pixels
    normalised_diff = average_diff / 255
    return normalised_diff


def process_images(
    directory, target_image_summary: Image.Image, threshold=0.07
) -> list[str]:
    count = 0
    failures: list[str] = []
    # Traverse the directory recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            count += 1

            # Check if the file is a JPEG or PNG image
            if file.lower().endswith((".jpeg", ".jpg")) and not file.startswith("."):
                candidate_filepath = os.path.join(root, file)
                try:
                    with Image.open(candidate_filepath) as candidate:
                        candidate_summary = summarise(candidate)
                        diff = difference(target_image_summary, candidate_summary)
                        if diff < threshold:
                            print(f'open "{candidate_filepath}" | diff {diff:0.2f}')
                except Image.DecompressionBombError:
                    print(f"too big: {candidate_filepath}")
                except OSError as ex:
                    failures.append(candidate_filepath)

    print(f"Processed {count} files; there were {len(failures)} failures")
    return failures


if __name__ == "__main__":
    import sys

    # configure
    matching_threshold = 0.06
    subject_image_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(
            "/Users/becky/Library/CloudStorage/Dropbox/Pictures/NY Alley at Night from Imgur.jpeg"
        )
    )
    target_dir_path = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else Path("/Users/becky/Library/CloudStorage/Dropbox/Pictures")
    )

    # Validate inputs
    if not subject_image_path.exists():
        print(f"Error: subject image not found: {subject_image_path}", file=sys.stderr)
        sys.exit(1)
    if not target_dir_path.is_dir():
        print(f"Error: target directory not found: {target_dir_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Looking for images similar to {subject_image_path} in {target_dir_path}")

    with Image.open(subject_image_path) as im:
        subject_summary = summarise(im)

    start = timer()
    fails = process_images(
        target_dir_path,
        target_image_summary=subject_summary,
        threshold=matching_threshold,
    )
    end = timer()
    delta = timedelta(seconds=end - start)
    print(f"\nexecution duration: {delta}")

    print(f"\n\n# list of all {len(fails)} failures:")
    json_data = json.dumps(fails, indent=4)

    # Printing the result
    print(pprint.pformat(json_data, indent=4, width=120))

    # Writing the result to a file
    with open("fails.json", "w") as file:
        file.write(json_data)
    print("###")
