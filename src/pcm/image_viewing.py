from pathlib import Path

import OpenImageIO as oiio
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def show_images(*paths: Path) -> None:
    bufs = [oiio.ImageBuf(str(p)) for p in paths]
    specs = [b.spec() for b in bufs]
    widths = [s.width for s in specs]
    height = max(s.height for s in specs)
    total_width = sum(widths)
    col_fractions = [w / total_width for w in widths]

    fig = make_subplots(rows=1, cols=len(bufs), column_widths=col_fractions,
                        horizontal_spacing=0)
    for col, (buf, spec) in enumerate(zip(bufs, specs), start=1):
        pixels = buf.get_pixels(oiio.FLOAT)
        trace = go.Image(z=(pixels.clip(0, 1) * 255).astype('uint8'))
        fig.add_trace(trace, row=1, col=col)

    fig.update_layout(
        width=total_width,
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    fig.show()


def show_image(path: Path) -> None:
    show_images(path)
