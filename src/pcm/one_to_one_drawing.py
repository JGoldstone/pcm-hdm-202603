from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def build_guide_rgb(
    window_w: int,
    window_h: int,
    arrow_w: int,
    arrow_h: int,
    red_guard_w: int = 2,
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """
    Build a black RGB buffer with a white double-ended guide arrow and red guard columns.

    Returns:
        (rgb_buffer, safe_roi)

    `safe_roi` is `(x_begin, x_end, y_begin, y_end)`, in an OIIO-style convention
    where `end` is one past the last valid index.
    """
    if arrow_h < 3 or arrow_h % 2 == 0:
        raise ValueError("arrow_h must be an odd integer >= 3")
    if red_guard_w < 1:
        raise ValueError("red_guard_w must be >= 1")
    if window_w < arrow_w or window_h < arrow_h:
        raise ValueError("window must be at least as large as the arrow")

    head_len = arrow_h // 2 + 1
    if arrow_w < 2 * head_len + 1:
        raise ValueError("arrow_w is too small for this arrow_h")

    img = np.zeros((window_h, window_w, 3), dtype=np.uint8)

    # Plotly image origin is top-left; y increases downward.
    x0 = (window_w - arrow_w) // 2
    x1 = x0 + arrow_w - 1
    y0 = window_h - arrow_h * 3
    yc = y0 + arrow_h // 2

    if x0 < red_guard_w or (window_w - 1 - x1) < red_guard_w:
        raise ValueError("window side margins are too small for red guard columns")

    # Safe zone where user content can be added without touching arrow/guards.
    safe_x_begin = x0 + 10
    safe_x_end = x1 - 10
    safe_y_begin = 10
    safe_y_end = yc - (arrow_h // 2) - arrow_h * 3 - 10
    safe_roi = (safe_x_begin, safe_x_end, safe_y_begin, safe_y_end)

    for i in range(head_len):
        half = i
        ys = yc - half
        ye = yc + half + 1
        img[ys:ye, x0 + i, :] = 255
        img[ys:ye, x1 - i, :] = 255

    shaft_start = x0 + head_len
    shaft_end = x1 - head_len
    if shaft_start <= shaft_end:
        img[y0 : y0 + arrow_h, shaft_start : shaft_end + 1, :] = 255

    # Red guard columns immediately beyond tips.
    img[:, x0 - red_guard_w : x0, 0] = 255
    img[:, x1 + 1 : x1 + 1 + red_guard_w, 0] = 255

    return img, safe_roi


def copy_array_into_rgb_buffer(
    rgb_buffer: np.ndarray,
    array_to_copy: np.ndarray,
    x_begin: int,
    y_begin: int,
) -> tuple[int, int, int, int]:
    """
    Copy a 2D or 3D array into an RGB uint8 buffer at `(x_begin, y_begin)`.

    Accepted `array_to_copy` formats:
    - (H, W): grayscale values in 0..1 or 0..255
    - (H, W, 1): same as grayscale
    - (H, W, 3): RGB in 0..1 or 0..255

    Returns the inserted region as `(x_begin, x_end, y_begin, y_end)`.
    """
    if rgb_buffer.ndim != 3 or rgb_buffer.shape[2] != 3:
        raise ValueError("rgb_buffer must have shape (H, W, 3)")

    patch = np.asarray(array_to_copy)
    if patch.ndim == 2:
        patch = patch[:, :, None]
    if patch.ndim != 3:
        raise ValueError("array_to_copy must be 2D or 3D")
    if patch.shape[2] == 1:
        patch = np.repeat(patch, 3, axis=2)
    elif patch.shape[2] != 3:
        raise ValueError("array_to_copy channel dimension must be 1 or 3")

    patch = patch.astype(np.float32, copy=False)
    if patch.size == 0:
        raise ValueError("array_to_copy is empty")

    # If values look normalized, scale to byte range.
    if np.nanmin(patch) >= 0.0 and np.nanmax(patch) <= 1.0:
        patch = patch * 255.0
    patch_u8 = np.clip(np.rint(patch), 0, 255).astype(np.uint8)

    patch_h, patch_w, _ = patch_u8.shape
    x_end = x_begin + patch_w
    y_end = y_begin + patch_h

    if x_begin < 0 or y_begin < 0 or x_end > rgb_buffer.shape[1] or y_end > rgb_buffer.shape[0]:
        raise ValueError("array_to_copy placement exceeds rgb_buffer bounds")

    rgb_buffer[y_begin:y_end, x_begin:x_end, :] = patch_u8
    return (x_begin, x_end, y_begin, y_end)


def show_rgb_buffer_plotly_strict(
    rgb_buffer: np.ndarray,
    *,
    show: bool = True,
    display_mode_bar: bool = False,
    responsive: bool = False,
) -> go.Figure:
    """
    Display an RGB buffer in Plotly with fixed-size, no-margin, strict layout settings.
    """
    if rgb_buffer.ndim != 3 or rgb_buffer.shape[2] != 3:
        raise ValueError("rgb_buffer must have shape (H, W, 3)")

    h, w, _ = rgb_buffer.shape
    fig = go.Figure(go.Image(z=rgb_buffer))
    fig.update_layout(
        width=w,
        height=h,
        autosize=False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="black",
        plot_bgcolor="black",
    )
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False, visible=False, constrain="domain")
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False, visible=False, scaleanchor="x")
    if show:
        fig.show(config={"displayModeBar": display_mode_bar, "responsive": responsive})
    return fig
