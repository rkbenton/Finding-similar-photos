"""Tests for the similarity module."""

# Import the functions we want to test from the src package.
# We use importlib so the tests don't depend on PYTHONPATH setup.
import importlib
import sys
from pathlib import Path

import pytest
from PIL import Image

src_path = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_path))

from similarity import difference, explore_directory, summarise  # noqa: E402

# ── summarise ────────────────────────────────────────────────────────────────


class TestSummarise:
    """Tests for the summarise() function."""

    def test_returns_16x16_image(self):
        """A 100x100 image should be resized to 16x16."""
        img = Image.new("RGB", (100, 100), color="red")
        result = summarise(img)
        assert result.size == (16, 16)

    def test_converts_rgba_to_rgb(self):
        """RGBA images should be converted to RGB before resizing."""
        img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 255))
        result = summarise(img)
        assert result.mode == "RGB"

    def test_converts_palette_to_rgb(self):
        """Palette-mode images should be converted to RGB."""
        img = Image.new("P", (50, 50), color=0)
        result = summarise(img)
        assert result.mode == "RGB"

    def test_preserves_color_mean(self):
        """A solid-colour image should keep its mean colour after summarising."""
        original = Image.new("RGB", (100, 100), color=(128, 64, 200))
        result = summarise(original)
        # All pixels should still be the same colour (16x16 of the same colour).
        assert list(result.get_flattened_data()) == [(128, 64, 200)] * 256


# ── difference ───────────────────────────────────────────────────────────────


class TestDifference:
    """Tests for the difference() function."""

    def test_identical_images_have_zero_difference(self):
        """Two identical images should return a difference of 0.0."""
        img1 = Image.new("RGB", (16, 16), color=(100, 150, 200))
        img2 = Image.new("RGB", (16, 16), color=(100, 150, 200))
        assert difference(img1, img2) == pytest.approx(0.0, abs=1e-9)

    def test_completely_different_images_return_one(self):
        """Black vs white should return a normalised difference of 1.0."""
        black = Image.new("RGB", (16, 16), color=(0, 0, 0))
        white = Image.new("RGB", (16, 16), color=(255, 255, 255))
        assert difference(black, white) == pytest.approx(1.0, abs=1e-9)

    def test_difference_is_symmetric(self):
        """difference(A, B) should equal difference(B, A)."""
        a = Image.new("RGB", (16, 16), color=(50, 100, 150))
        b = Image.new("RGB", (16, 16), color=(200, 50, 100))
        assert difference(a, b) == pytest.approx(difference(b, a))

    def test_difference_is_between_zero_and_one(self):
        """Normalised difference should always be in [0, 1]."""
        img1 = Image.new("RGB", (16, 16), color=(30, 70, 110))
        img2 = Image.new("RGB", (16, 16), color=(220, 180, 90))
        diff = difference(img1, img2)
        assert 0.0 <= diff <= 1.0

    def test_halfway_colour_gives_half_difference(self):
        """A colour that is exactly halfway should give ~0.5 difference."""
        black = Image.new("RGB", (16, 16), color=(0, 0, 0))
        grey = Image.new("RGB", (16, 16), color=(128, 128, 128))
        assert difference(black, grey) == pytest.approx(0.5, abs=1e-2)


# ── explore_directory ────────────────────────────────────────────────────────


class TestExploreDirectory:
    """Tests for the explore_directory() function.

    We use the bundled test images in the `dublin` and `seagulls` directories
    so no external downloads are needed.
    """

    @pytest.fixture()
    def dublin_dir(self) -> Path:
        return Path(__file__).resolve().parents[1] / "dublin"

    @pytest.fixture()
    def seagulls_dir(self) -> Path:
        return Path(__file__).resolve().parents[1] / "seagulls"

    def test_finds_images_in_directory(self, dublin_dir):
        """The function should discover all images in the given directory."""
        files = list(dublin_dir.glob("*.jpg")) + list(dublin_dir.glob("*.jpeg"))
        assert len(files) > 0

    def test_finds_similar_images_in_seagulls(self, seagulls_dir, capsys):
        """Seagull images are similar to each other and should be flagged."""
        explore_directory(seagulls_dir)
        captured = capsys.readouterr()
        # At least one pair should be flagged as near-duplicate.
        assert "Near-duplicates found:" in captured.out
        assert "###" in captured.out

    def test_finds_similar_images_in_dublin(self, dublin_dir, capsys):
        """Dublin images contain some similar pairs that should be flagged."""
        explore_directory(dublin_dir)
        captured = capsys.readouterr()
        assert "Near-duplicates found:" in captured.out
        assert "###" in captured.out

    def test_exits_cleanly_on_empty_directory(self, tmp_path, capsys):
        """An empty directory should not raise an error."""
        explore_directory(tmp_path)
        captured = capsys.readouterr()
        assert captured.err == ""  # no stderr
