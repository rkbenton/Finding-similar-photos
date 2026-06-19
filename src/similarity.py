from itertools import combinations
from pathlib import Path

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

    # Use get_flattened_data() for a much faster iteration than nested loops + getpixel()
    total = sum((r + g + b) / 3 for r, g, b in diff.get_flattened_data())
    num_pixels = diff.width * diff.height
    average_diff = total / num_pixels
    normalised_diff = average_diff / 255
    return normalised_diff


def explore_directory(path: Path) -> None:
    """Find images in a directory and compare them all."""

    files = (
        list(path.glob("*.jpg")) + list(path.glob("*.jpeg")) + list(path.glob("*.png"))
    )
    diffs = {}

    summaries = []
    for file in files:
        try:
            with Image.open(file) as img:
                summaries.append((file, summarise(img)))
        except Image.DecompressionBombError:
            print(f"too big: {file}")
        except OSError as ex:
            print(f"failed to open {file}: {ex}")

    for (f1, sum1), (f2, sum2) in combinations(summaries, r=2):
        key = tuple(sorted([str(f1), str(f2)]))

        diff = difference(sum1, sum2)
        print(key, diff)
        diffs[key] = diff

    print()
    print("Near-duplicates found:")
    print("======================")
    for key, diff in diffs.items():
        if diff < 0.07:
            print(key)
    print("###")


if __name__ == "__main__":
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else Path("dublin")
    explore_directory(target_dir)
