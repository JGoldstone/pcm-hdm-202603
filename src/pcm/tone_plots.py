from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, Sequence

import numpy as np
import plotly.graph_objects as go
from plotly.colors import qualitative


@dataclass(frozen=True)
class ToneTrace:
    name: str
    color: str | None
    data: Sequence[tuple[float, float]]


def _ceil_to_half(value: float) -> float:
    return ceil(value * 2.0) / 2.0


def _normalize_traces(traces: Iterable[dict]) -> list[ToneTrace]:
    normalized: list[ToneTrace] = []
    for i, trace in enumerate(traces):
        missing = [k for k in ("name", "color", "data") if k not in trace]
        if missing:
            raise ValueError(f"Trace index {i} missing required keys: {missing}")
        data = trace["data"]
        if len(data) == 0:
            raise ValueError(f"Trace index {i} has empty data.")
        normalized.append(
            ToneTrace(
                name=str(trace["name"]),
                color=None if trace["color"] is None else str(trace["color"]),
                data=tuple((float(x), float(y)) for x, y in data),
            )
        )
    return normalized


def _gradient_shapes(
    *,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    horizontal: bool,
    reverse: bool = False,
    steps: int = 128,
) -> list[dict]:
    shapes: list[dict] = []
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        g = int(round((1.0 - t0 if reverse else t0) * 230))
        color = f"rgb({g},{g},{g})"
        if horizontal:
            xa0 = x0 + (x1 - x0) * t0
            xa1 = x0 + (x1 - x0) * t1
            ya0, ya1 = y0, y1
        else:
            ya0 = y0 + (y1 - y0) * t0
            ya1 = y0 + (y1 - y0) * t1
            xa0, xa1 = x0, x1
        shapes.append(
            {
                "type": "rect",
                "xref": "paper",
                "yref": "paper",
                "x0": xa0,
                "x1": xa1,
                "y0": ya0,
                "y1": ya1,
                "line": {"width": 0},
                "fillcolor": color,
                "layer": "below",
            }
        )
    return shapes


def _label_color_from_fraction(fraction: float) -> str:
    # White text on darker half of the grayscale strip, black on lighter half.
    return "white" if fraction < 0.5 else "black"


def _build_ticktext(values: Sequence[float], vmin: float, vmax: float) -> list[str]:
    span = max(vmax - vmin, 1e-12)
    labels = []
    for v in values:
        frac = (v - vmin) / span
        c = _label_color_from_fraction(frac)
        labels.append(f"<span style='color:{c}'>{v:.1f}</span>")
    return labels


def _base_figure(
    *,
    x_major_label: str,
    x_minor_label: str,
    y_major_label: str,
) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgb(235,235,235)",
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(x=0.53, y=0.93, bgcolor="rgba(255,255,255,0)"),
        margin=dict(l=140, r=40, t=40, b=120),
        xaxis=dict(
            title=f"<b>{x_major_label}</b><br><i>{x_minor_label}</i>",
            ticks="inside",
            ticklen=12,
            tickwidth=2,
            mirror=True,
            showgrid=True,
            gridcolor="rgba(180,180,180,0.8)",
            gridwidth=1.2,
            minor=dict(
                ticks="inside",
                ticklen=6,
                tickwidth=1.5,
                showgrid=True,
                gridcolor="rgba(180,180,180,0.45)",
                gridwidth=0.8,
            ),
            ticklabeloverflow="allow",
        ),
        yaxis=dict(
            title=f"<b>{y_major_label}</b>",
            ticks="inside",
            ticklen=12,
            tickwidth=2,
            mirror=True,
            showgrid=True,
            gridcolor="rgba(180,180,180,0.8)",
            gridwidth=1.2,
            minor=dict(
                ticks="inside",
                ticklen=6,
                tickwidth=1.5,
                showgrid=True,
                gridcolor="rgba(180,180,180,0.45)",
                gridwidth=0.8,
            ),
            ticklabeloverflow="allow",
        ),
    )
    return fig


def _add_external_grayscale_bars_linlin(fig: go.Figure) -> tuple[list[float], list[float], list[float], list[float]]:
    # Domains are arranged so the gradient strips are outside but directly abutting the data axes.
    # Keep the main data area square, leave side/top/bottom breathing room, and
    # use equal strip thickness for left and bottom gradients.
    outer_left = 0.052
    outer_right = 0.04
    outer_top = 0.04
    outer_bottom = 0.052
    bar_t = 0.048

    data_x0 = outer_left + bar_t
    data_x1 = 1.0 - outer_right
    data_y0 = outer_bottom + bar_t
    data_y1 = 1.0 - outer_top

    data_x_domain = [data_x0, data_x1]
    data_y_domain = [data_y0, data_y1]
    left_bar_x_domain = [outer_left, data_x0]
    bottom_bar_y_domain = [outer_bottom, data_y0]

    fig.update_layout(
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(domain=data_x_domain, constrain="domain"),
        yaxis=dict(domain=data_y_domain, constrain="domain"),
        xaxis2=dict(domain=data_x_domain, anchor="y2", visible=False, fixedrange=True, range=[0.0, 1.0]),
        yaxis2=dict(domain=bottom_bar_y_domain, anchor="x2", visible=False, fixedrange=True),
        xaxis3=dict(domain=left_bar_x_domain, anchor="y3", visible=False, fixedrange=True),
        yaxis3=dict(domain=data_y_domain, anchor="x3", visible=False, fixedrange=True, range=[0.0, 1.0]),
    )

    gradient_steps = 256
    x_gradient = np.linspace(0.0, 1.0, gradient_steps, dtype=float).reshape(1, -1)
    y_gradient = np.linspace(0.0, 1.0, gradient_steps, dtype=float).reshape(-1, 1)
    gray_scale = [[0.0, "rgb(0,0,0)"], [1.0, "rgb(230,230,230)"]]

    fig.add_trace(
        go.Heatmap(
            z=x_gradient,
            colorscale=gray_scale,
            showscale=False,
            hoverinfo="skip",
            x=np.linspace(0.0, 1.0, gradient_steps),
            y=[0.0],
            xaxis="x2",
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Heatmap(
            z=y_gradient,
            colorscale=gray_scale,
            showscale=False,
            hoverinfo="skip",
            x=[0.0],
            y=np.linspace(0.0, 1.0, gradient_steps),
            xaxis="x3",
            yaxis="y3",
        )
    )
    return data_x_domain, data_y_domain, left_bar_x_domain, bottom_bar_y_domain


def _add_external_grayscale_bars_log(fig: go.Figure, limit: float) -> tuple[list[float], list[float], list[float], list[float]]:
    # Match the tuned lin-lin geometry so both figure styles feel consistent.
    outer_left = 0.052
    outer_right = 0.04
    outer_top = 0.04
    outer_bottom = 0.052
    bar_t = 0.048

    data_x0 = outer_left + bar_t
    data_x1 = 1.0 - outer_right
    data_y0 = outer_bottom + bar_t
    data_y1 = 1.0 - outer_top

    data_x_domain = [data_x0, data_x1]
    data_y_domain = [data_y0, data_y1]
    left_bar_x_domain = [outer_left, data_x0]
    bottom_bar_y_domain = [outer_bottom, data_y0]

    fig.update_layout(
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(domain=data_x_domain, constrain="domain"),
        yaxis=dict(domain=data_y_domain, constrain="domain"),
        xaxis2=dict(domain=data_x_domain, anchor="y2", visible=False, fixedrange=True, range=[-limit, 0.0]),
        yaxis2=dict(domain=bottom_bar_y_domain, anchor="x2", visible=False, fixedrange=True),
        xaxis3=dict(domain=left_bar_x_domain, anchor="y3", visible=False, fixedrange=True),
        yaxis3=dict(domain=data_y_domain, anchor="x3", visible=False, fixedrange=True, range=[0.0, limit]),
    )

    gradient_steps = 256
    x_gradient = np.linspace(0.0, 1.0, gradient_steps, dtype=float).reshape(1, -1)
    y_gradient = np.linspace(0.0, 1.0, gradient_steps, dtype=float).reshape(-1, 1)
    gray_scale_x = [[0.0, "rgb(0,0,0)"], [1.0, "rgb(230,230,230)"]]
    gray_scale_y = [[0.0, "rgb(230,230,230)"], [1.0, "rgb(0,0,0)"]]

    fig.add_trace(
        go.Heatmap(
            z=x_gradient,
            colorscale=gray_scale_x,
            showscale=False,
            hoverinfo="skip",
            x=np.linspace(-limit, 0.0, gradient_steps),
            y=[0.0],
            xaxis="x2",
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Heatmap(
            z=y_gradient,
            colorscale=gray_scale_y,
            showscale=False,
            hoverinfo="skip",
            x=[0.0],
            y=np.linspace(0.0, limit, gradient_steps),
            xaxis="x3",
            yaxis="y3",
        )
    )
    return data_x_domain, data_y_domain, left_bar_x_domain, bottom_bar_y_domain


def make_luminance_plot_linlin(
    traces: Iterable[dict],
    *,
    x_major_label: str,
    x_minor_label: str,
    y_major_label: str,
) -> go.Figure:
    """
    Plot linear scene luminance factor (x) versus reproduced luminance factor (y).

    `traces` is an iterable of dicts with keys: `name`, `color`, `data`.
    `data` should be a sequence of `(x, y)` tuples.
    """
    tdata = _normalize_traces(traces)
    fig = _base_figure(
        x_major_label=x_major_label,
        x_minor_label=x_minor_label,
        y_major_label=y_major_label,
    )

    palette = qualitative.Plotly
    for i, trace in enumerate(tdata):
        x, y = zip(*trace.data)
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=trace.name,
                line=dict(color=trace.color or palette[i % len(palette)], width=5),
            )
        )

    major_ticks = np.arange(0.0, 1.0001, 0.2)
    fig.update_xaxes(
        range=[0.0, 1.0],
        dtick=0.2,
        minor=dict(dtick=0.1),
        tickmode="array",
        tickvals=major_ticks,
        showticklabels=False,
    )
    fig.update_yaxes(
        range=[0.0, 1.0],
        dtick=0.2,
        minor=dict(dtick=0.1),
        tickmode="array",
        tickvals=major_ticks,
        showticklabels=False,
        constrain="domain",
    )

    fig.update_xaxes(
        ticklabelposition="outside",
        ticklabelstandoff=10,
        title_standoff=48,
    )
    fig.update_yaxes(
        ticklabelposition="outside",
        ticklabelstandoff=8,
        title_standoff=48,
    )

    _, _, left_bar_x_domain, bottom_bar_y_domain = _add_external_grayscale_bars_linlin(fig)

    # Draw major tick labels as annotations on top of gradient bars so traces cannot obscure them.
    # Place labels slightly closer to the grid-facing edge of each strip.
    x_bar_h = bottom_bar_y_domain[1] - bottom_bar_y_domain[0]
    y_bar_w = left_bar_x_domain[1] - left_bar_x_domain[0]
    x_tick_y = bottom_bar_y_domain[0] + 0.50 * x_bar_h
    y_tick_x = left_bar_x_domain[0] + 0.68 * y_bar_w
    annotations: list[dict] = []
    for t in major_ticks:
        c = _label_color_from_fraction(float(t))
        x_anchor = "left" if np.isclose(t, 0.0) else "center"
        x_shift = 4 if np.isclose(t, 0.0) else 0
        annotations.append(
            dict(
                x=float(t),
                y=x_tick_y,
                xref="x",
                yref="paper",
                text=f"<span style='color:{c}'>{t:.1f}</span>",
                showarrow=False,
                xanchor=x_anchor,
                yanchor="middle",
                xshift=x_shift,
                font=dict(size=20),
            )
        )
        y_anchor = "bottom" if np.isclose(t, 0.0) else "middle"
        y_shift = 4 if np.isclose(t, 0.0) else 0
        annotations.append(
            dict(
                x=y_tick_x,
                y=float(t),
                xref="paper",
                yref="y",
                text=f"<span style='color:{c}'>{t:.1f}</span>",
                showarrow=False,
                xanchor="center",
                yanchor=y_anchor,
                xshift=-8,
                yshift=y_shift,
                font=dict(size=20),
            )
        )
    fig.update_layout(annotations=annotations)
    return fig


def make_luminance_plot_log(
    traces: Iterable[dict],
    *,
    x_major_label: str,
    x_minor_label: str,
    y_major_label: str,
) -> go.Figure:
    """
    Plot log10(scene luminance factor) on x against -log10(reproduced luminance factor) on y.

    `traces` is an iterable of dicts with keys: `name`, `color`, `data`.
    `data` should be a sequence of `(scene_luminance, reproduced_luminance)` tuples.
    All values must be > 0.
    """
    tdata = _normalize_traces(traces)
    fig = _base_figure(
        x_major_label=x_major_label,
        x_minor_label=x_minor_label,
        y_major_label=y_major_label,
    )

    palette = qualitative.Plotly
    x_all: list[float] = []
    y_all: list[float] = []
    for i, trace in enumerate(tdata):
        x_lin, y_lin = zip(*trace.data)
        x_lin_arr = np.asarray(x_lin, dtype=float)
        y_lin_arr = np.asarray(y_lin, dtype=float)
        if np.any(x_lin_arr <= 0.0) or np.any(y_lin_arr <= 0.0):
            raise ValueError("Log plot requires strictly positive scene and reproduced luminance values.")

        x_log = np.log10(x_lin_arr)
        y_log = -np.log10(y_lin_arr)
        x_all.extend(x_log.tolist())
        y_all.extend(y_log.tolist())

        fig.add_trace(
            go.Scatter(
                x=x_log,
                y=y_log,
                mode="lines",
                name=trace.name,
                line=dict(color=trace.color or palette[i % len(palette)], width=5),
            )
        )

    x_left = _ceil_to_half(abs(min(x_all)))
    y_top = _ceil_to_half(max(y_all))
    limit = max(x_left, y_top, 0.5)

    major_ticks_x = np.arange(-limit, 0.0001, 1.0)
    major_ticks_y = np.arange(0.0, limit + 1e-9, 1.0)
    fig.update_xaxes(
        range=[-limit, 0.0],
        dtick=1.0,
        minor=dict(dtick=0.25),
        tickmode="array",
        tickvals=major_ticks_x,
        showticklabels=False,
    )
    fig.update_yaxes(
        range=[0.0, limit],
        dtick=1.0,
        minor=dict(dtick=0.25),
        tickmode="array",
        tickvals=major_ticks_y,
        showticklabels=False,
        constrain="domain",
    )

    fig.update_xaxes(
        ticklabelposition="outside",
        ticklabelstandoff=10,
        title_standoff=48,
    )
    fig.update_yaxes(
        ticklabelposition="outside",
        ticklabelstandoff=8,
        title_standoff=48,
    )

    _, _, left_bar_x_domain, bottom_bar_y_domain = _add_external_grayscale_bars_log(fig, limit)

    x_bar_h = bottom_bar_y_domain[1] - bottom_bar_y_domain[0]
    y_bar_w = left_bar_x_domain[1] - left_bar_x_domain[0]
    x_tick_y = bottom_bar_y_domain[0] + 0.50 * x_bar_h
    y_tick_x = left_bar_x_domain[0] + 0.68 * y_bar_w
    annotations: list[dict] = []

    x_span = max(limit, 1e-12)
    for t in major_ticks_x:
        frac = (float(t) + limit) / x_span
        c = _label_color_from_fraction(frac)
        is_left_edge = np.isclose(t, -limit)
        is_right_edge = np.isclose(t, 0.0)
        x_anchor = "left" if is_left_edge else ("right" if is_right_edge else "center")
        x_shift = 4 if is_left_edge else (-4 if is_right_edge else 0)
        annotations.append(
            dict(
                x=float(t),
                y=x_tick_y,
                xref="x",
                yref="paper",
                text=f"<span style='color:{c}'>{t:.1f}</span>",
                showarrow=False,
                xanchor=x_anchor,
                yanchor="middle",
                xshift=x_shift,
                font=dict(size=20),
            )
        )

    for t in major_ticks_y:
        frac = float(t) / x_span
        c = _label_color_from_fraction(1.0 - frac)
        is_bottom_edge = np.isclose(t, 0.0)
        is_top_edge = np.isclose(t, limit)
        y_anchor = "bottom" if is_bottom_edge else ("top" if is_top_edge else "middle")
        y_shift = 4 if is_bottom_edge else (-4 if is_top_edge else 0)
        annotations.append(
            dict(
                x=y_tick_x,
                y=float(t),
                xref="paper",
                yref="y",
                text=f"<span style='color:{c}'>{t:.1f}</span>",
                showarrow=False,
                xanchor="center",
                yanchor=y_anchor,
                xshift=-8,
                yshift=y_shift,
                font=dict(size=20),
            )
        )

    fig.update_layout(annotations=annotations)
    return fig
