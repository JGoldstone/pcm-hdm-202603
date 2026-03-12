"""Image resizing helpers backed by OpenImageIO."""

import math
from pathlib import Path

import OpenImageIO as oiio


def resize_image(
    in_path: Path,
    out_path: Path,
    scale_factor: float,
) -> None:
    """Resize an image by ``scale_factor`` and write the result to ``out_path``."""

    if not math.isfinite(scale_factor) or scale_factor <= 0:
        raise ValueError(f"scale_factor must be finite and > 0, got {scale_factor}")

    if not in_path.exists():
        raise FileNotFoundError(f"Input image does not exist: {in_path}")
    if not in_path.is_file():
        raise ValueError(f"Input path is not a file: {in_path}")

    # OIIO Python bindings are typed for str paths.
    in_buf = oiio.ImageBuf(str(in_path))
    if in_buf.has_error:
        raise RuntimeError(f"Failed to load input image: {in_path}\n{in_buf.geterror()}")

    spec = in_buf.spec()
    if spec.width <= 0 or spec.height <= 0:
        raise RuntimeError(
            f"Invalid input image dimensions ({spec.width}x{spec.height}) for {in_path}"
        )

    new_w = max(1, int(round(spec.width * scale_factor)))
    new_h = max(1, int(round(spec.height * scale_factor)))

    roi = oiio.ROI(
        spec.x,
        spec.x + new_w,
        spec.y,
        spec.y + new_h,
        spec.z,
        spec.z + spec.depth,
        0,  # chbegin
        spec.nchannels,  # chend
    )

    resized_buf = oiio.ImageBufAlgo.resize(in_buf, roi=roi)
    if resized_buf.has_error:
        raise RuntimeError(f"Resize failed for {in_path}\n{resized_buf.geterror()}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = resized_buf.write(str(out_path))
    if not ok or resized_buf.has_error:
        raise RuntimeError(
            f"Failed to write output image: {out_path}\n{resized_buf.geterror()}"
        )
