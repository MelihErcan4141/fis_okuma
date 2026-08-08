from pathlib import Path

import pytest
from PIL import Image

from image.preprocessor import ImagePreprocessor


def create_test_image(path, mode="RGB"):
    image = Image.new(mode, (100, 100))
    image.save(path)


def test_jpg_is_processed(tmp_path):
    source = tmp_path / "test.jpg"
    create_test_image(source)

    preprocessor = ImagePreprocessor()

    result = preprocessor.prepare(str(source))

    result_path = Path(result)

    assert result_path.exists()
    assert result_path.suffix == ".jpg"


def test_png_is_converted_to_jpg(tmp_path):
    source = tmp_path / "test.png"
    create_test_image(source)

    preprocessor = ImagePreprocessor()

    result = preprocessor.prepare(str(source))

    result_path = Path(result)

    assert result_path.exists()
    assert result_path.suffix == ".jpg"


def test_rgba_png_is_converted_to_rgb_jpg(tmp_path):
    source = tmp_path / "transparent.png"
    create_test_image(source, mode="RGBA")

    preprocessor = ImagePreprocessor()

    result = preprocessor.prepare(str(source))

    with Image.open(result) as image:
        assert image.mode == "RGB"


def test_missing_file_raises_error(tmp_path):
    source = tmp_path / "does_not_exist.jpg"

    preprocessor = ImagePreprocessor()

    with pytest.raises(FileNotFoundError):
        preprocessor.prepare(str(source))


def test_unsupported_extension_raises_error(tmp_path):
    source = tmp_path / "receipt.txt"
    source.write_text("test")

    preprocessor = ImagePreprocessor()

    with pytest.raises(ValueError):
        preprocessor.prepare(str(source))



def test_large_image_is_resized(tmp_path):
    image_path = tmp_path / "large.jpg"

    image = Image.new(
        "RGB",
        (3024, 4032),
        "white"
    )

    image.save(image_path)

    preprocessor = ImagePreprocessor()

    result_path = preprocessor.prepare(
        str(image_path)
    )

    with Image.open(result_path) as result:
        width, height = result.size

    assert max(width, height) == 2200

    # Aspect ratio korunmalı.
    assert width == 1650
    assert height == 2200


def test_small_image_is_not_upscaled(tmp_path):
    image_path = tmp_path / "small.jpg"

    image = Image.new(
        "RGB",
        (800, 1200),
        "white"
    )

    image.save(image_path)

    preprocessor = ImagePreprocessor()

    result_path = preprocessor.prepare(
        str(image_path)
    )

    with Image.open(result_path) as result:
        width, height = result.size

    assert width == 800
    assert height == 1200