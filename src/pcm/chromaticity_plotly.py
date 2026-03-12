from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import plotly.graph_objects as go
from colour import xy_to_Luv_uv
from colour.plotting.diagrams import (
    LABELS_CHROMATICITY_DIAGRAM_DEFAULT,
    lines_spectral_locus,
)

ChromaticityPoint = tuple[float, float]
ChromaticityTriangle = tuple[ChromaticityPoint, ChromaticityPoint, ChromaticityPoint]


def _normalise_colorspace(colorspace: str) -> str:
    normalised = colorspace.strip().lower()
    if normalised not in {"xy", "uv"}:
        raise ValueError("colorspace must be either 'xy' or 'uv'.")
    return normalised


def _to_plot_coords(points_xy: np.ndarray, colorspace: str) -> np.ndarray:
    if colorspace == "xy":
        return points_xy
    return np.asarray(xy_to_Luv_uv(points_xy), dtype=np.float64)


def draw_chromaticity_diagram(
    *,
    colorspace: str = "xy",
    spectral_locus_labels: Sequence[int] | None = None,
    title: str | None = None,
    width: int = 850,
    height: int = 850,
) -> go.Figure:
    """Return a Plotly chromaticity diagram with spectral-locus labels only."""

    colorspace = _normalise_colorspace(colorspace)
    method = "CIE 1931" if colorspace == "xy" else "CIE 1976 UCS"

    if spectral_locus_labels is None:
        spectral_locus_labels = LABELS_CHROMATICITY_DIAGRAM_DEFAULT[method]

    lines_sl, lines_w = lines_spectral_locus(
        labels=tuple(spectral_locus_labels),
        method=method,
    )

    locus_positions = np.asarray(lines_sl["position"], dtype=np.float64)
    label_positions = np.asarray(lines_w["position"][::2], dtype=np.float64)
    label_normals = np.asarray(lines_w["normal"][::2], dtype=np.float64)

    if title is None:
        title = (
            "CIE 1931 Chromaticity Diagram"
            if colorspace == "xy"
            else "CIE 1976 u'v' Chromaticity Diagram"
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=locus_positions[:, 0],
            y=locus_positions[:, 1],
            mode="lines",
            line={"color": "black", "width": 2},
            name="Spectral Locus",
            hovertemplate="x=%{x:.4f}<br>y=%{y:.4f}<extra></extra>",
        )
    )

    tick_segments_x: list[float | None] = []
    tick_segments_y: list[float | None] = []
    for i in range(0, len(lines_w["position"]), 2):
        p0 = lines_w["position"][i]
        p1 = lines_w["position"][i + 1]
        tick_segments_x.extend([float(p0[0]), float(p1[0]), None])
        tick_segments_y.extend([float(p0[1]), float(p1[1]), None])

    fig.add_trace(
        go.Scatter(
            x=tick_segments_x,
            y=tick_segments_y,
            mode="lines",
            line={"color": "black", "width": 1},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    label_offset = 1.25 / 50.0
    text_x = label_positions[:, 0] + label_normals[:, 0] * label_offset
    text_y = label_positions[:, 1] + label_normals[:, 1] * label_offset
    text_position = [
        "middle left" if normal[0] >= 0 else "middle right"
        for normal in label_normals
    ]

    fig.add_trace(
        go.Scatter(
            x=text_x,
            y=text_y,
            mode="text",
            text=[str(wl) for wl in spectral_locus_labels],
            textposition=text_position,
            textfont={"size": 11, "color": "black"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    xaxis_range = [0, 1] if colorspace == "xy" else [0, 0.7]
    yaxis_range = [0, 1] if colorspace == "xy" else [0, 0.7]
    xaxis_label = "CIE x" if colorspace == "xy" else "CIE u'"
    yaxis_label = "CIE y" if colorspace == "xy" else "CIE v'"

    fig.update_layout(
        title=title,
        template="plotly_white",
        width=width,
        height=height,
        xaxis={"title": xaxis_label, "range": xaxis_range, "zeroline": False},
        yaxis={
            "title": yaxis_label,
            "range": yaxis_range,
            "zeroline": False,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        meta={"pcm_colorspace": colorspace},
    )

    return fig


def add_chromaticity_points(
    figure: go.Figure,
    points: Mapping[str, ChromaticityPoint],
    *,
    colorspace: str | None = None,
    marker_color: str = "black",
    marker_size: float = 10,
) -> go.Figure:
    """Add labelled chromaticity points to a figure and return it."""

    if colorspace is None:
        figure_colorspace = (figure.layout.meta or {}).get("pcm_colorspace", "xy")
        colorspace = str(figure_colorspace)
    colorspace = _normalise_colorspace(colorspace)

    if not points:
        return figure

    labels = list(points.keys())
    xy = np.asarray(list(points.values()), dtype=np.float64)
    plot_points = _to_plot_coords(xy, colorspace)

    figure.add_trace(
        go.Scatter(
            x=plot_points[:, 0],
            y=plot_points[:, 1],
            mode="markers",
            marker={"size": marker_size, "color": marker_color},
            customdata=np.asarray(labels, dtype=object),
            name="Chromaticity Points",
            hovertemplate="<b>%{customdata}</b><br>x=%{x:.4f}<br>y=%{y:.4f}<extra></extra>",
        )
    )

    return figure


def add_gamut_triangles(
    figure: go.Figure,
    gamuts: Mapping[str, Mapping[str, object]],
    *,
    colorspace: str | None = None,
    line_width: float = 2.5,
) -> go.Figure:
    """Add gamut triangles to a figure and return it."""

    if colorspace is None:
        figure_colorspace = (figure.layout.meta or {}).get("pcm_colorspace", "xy")
        colorspace = str(figure_colorspace)
    colorspace = _normalise_colorspace(colorspace)

    for gamut_name, gamut_data in gamuts.items():
        if "triangle" not in gamut_data:
            raise KeyError(f"Gamut '{gamut_name}' is missing required key 'triangle'.")

        triangle = np.asarray(gamut_data["triangle"], dtype=np.float64)
        if triangle.shape != (3, 2):
            raise ValueError(
                f"Gamut '{gamut_name}' triangle must be 3 coordinate pairs."
            )

        color = str(gamut_data.get("color", "black"))

        plot_triangle = _to_plot_coords(triangle, colorspace)
        closed = np.vstack([plot_triangle, plot_triangle[0]])
        figure.add_trace(
            go.Scatter(
                x=closed[:, 0],
                y=closed[:, 1],
                mode="lines",
                line={"color": color, "width": line_width},
                name=gamut_name,
                hovertemplate=f"{gamut_name}<br>x=%{{x:.4f}}<br>y=%{{y:.4f}}<extra></extra>",
            )
        )

    return figure


__all__ = [
    "add_chromaticity_points",
    "add_gamut_triangles",
    "draw_chromaticity_diagram",
]
