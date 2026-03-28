import pytest
from renderer import PetRenderer


def test_widget_width():
    # 8 cols * 12px + 7 gaps * 1px = 103
    renderer = PetRenderer()
    assert renderer.widget_width() == 103


def test_widget_height():
    # 6 rows * 12px + 5 gaps * 1px = 77
    renderer = PetRenderer()
    assert renderer.widget_height() == 77


def test_render_does_not_raise(qapp):
    from PyQt6.QtGui import QPainter, QPixmap
    from frames import FRAMES

    renderer = PetRenderer()
    pixmap = QPixmap(renderer.widget_width(), renderer.widget_height())
    pixmap.fill()
    painter = QPainter(pixmap)
    frame = FRAMES["idle"][0]
    renderer.render(painter, frame)
    painter.end()


def test_render_skips_transparent(qapp):
    from PyQt6.QtGui import QPainter, QPixmap

    renderer = PetRenderer()
    pixmap = QPixmap(renderer.widget_width(), renderer.widget_height())
    pixmap.fill()
    painter = QPainter(pixmap)
    frame = [["transparent"] * 8 for _ in range(6)]
    renderer.render(painter, frame)
    painter.end()
