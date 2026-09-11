"""Input, image and safe-rendering utilities; no network dependencies."""
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 24_000_000


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value: str, label: str, minimum: int, maximum: int) -> str:
    text = (value or "").strip()
    if not minimum <= len(text) <= maximum:
        raise ValueError(f"{label} must contain {minimum}–{maximum} characters.")
    if "\x00" in text:
        raise ValueError(f"{label} contains an unsupported character.")
    return text


def safe(value: object) -> str:
    return escape(str(value), quote=True)


def date_label(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%d %b %Y · %H:%M UTC")


def prepare_image(raw: bytes) -> tuple[bytes, bytes]:
    """Decode actual content, strip metadata, orient, resize and make thumbnail."""
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Choose an image smaller than 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as probe:
                if probe.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Please use a JPEG, PNG or WebP image.")
                if probe.width * probe.height > MAX_PIXELS:
                    raise ValueError("Choose an image with fewer than 24 megapixels.")
                probe.verify()
            with Image.open(BytesIO(raw)) as original:
                source = ImageOps.exif_transpose(original)
                source.thumbnail((1600, 1600))
                rgba = source.convert("RGBA")
                image = Image.new("RGB", rgba.size, "white")
                image.paste(rgba, mask=rgba.getchannel("A"))
                full = BytesIO()
                image.save(full, "JPEG", quality=85, optimize=True)
                thumb = ImageOps.fit(image, (640, 360))
                preview = BytesIO()
                thumb.save(preview, "JPEG", quality=80, optimize=True)
                return full.getvalue(), preview.getvalue()
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("This image cannot be opened. Try another JPEG, PNG or WebP.") from exc
