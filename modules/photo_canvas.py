"""Mouse editor for a fixed 1280x720 photo camera canvas."""

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget


class PhotoCanvas(QWidget):
    compositionChanged = Signal()
    OUTPUT_WIDTH = 1280
    OUTPUT_HEIGHT = 720
    HANDLE_SIZE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self._image = None
        self._composite = None
        self._rect = QRectF()
        self._gesture = None

    def set_image(self, image):
        self._image = image.copy()
        self.reset_fit()

    def reset_fit(self):
        if self._image is None:
            return
        scale = min(
            self.OUTPUT_WIDTH / self._image.width(),
            self.OUTPUT_HEIGHT / self._image.height(),
        )
        width, height = self._image.width() * scale, self._image.height() * scale
        self._rect = QRectF(
            (self.OUTPUT_WIDTH - width) / 2,
            (self.OUTPUT_HEIGHT - height) / 2,
            width,
            height,
        )
        self._gesture = None
        self._changed()

    def viewport_rect(self):
        scale = min(
            (self.width() - 16) / self.OUTPUT_WIDTH,
            (self.height() - 16) / self.OUTPUT_HEIGHT,
        )
        width, height = self.OUTPUT_WIDTH * scale, self.OUTPUT_HEIGHT * scale
        return QRectF(
            (self.width() - width) / 2, (self.height() - height) / 2, width, height
        )

    def _to_output(self, point):
        view = self.viewport_rect()
        return QPointF(
            (point.x() - view.x()) * self.OUTPUT_WIDTH / view.width(),
            (point.y() - view.y()) * self.OUTPUT_HEIGHT / view.height(),
        )

    def _screen_rect(self):
        view = self.viewport_rect()
        scale = view.width() / self.OUTPUT_WIDTH
        return QRectF(
            view.x() + self._rect.x() * scale,
            view.y() + self._rect.y() * scale,
            self._rect.width() * scale,
            self._rect.height() * scale,
        )

    def _corners(self):
        rect = self._screen_rect()
        return [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]

    def _handle_at(self, point):
        for index, corner in enumerate(self._corners()):
            if (
                abs(point.x() - corner.x()) <= self.HANDLE_SIZE
                and abs(point.y() - corner.y()) <= self.HANDLE_SIZE
            ):
                return index
        return None

    def _changed(self):
        # Keep some of the photo visible so it is always possible to drag it back.
        visible = min(32.0, self._rect.width() / 2, self._rect.height() / 2)
        self._rect.moveLeft(
            min(
                self.OUTPUT_WIDTH - visible,
                max(visible - self._rect.width(), self._rect.x()),
            )
        )
        self._rect.moveTop(
            min(
                self.OUTPUT_HEIGHT - visible,
                max(visible - self._rect.height(), self._rect.y()),
            )
        )
        self._composite = None
        self.update()
        self.compositionChanged.emit()

    def composed_image(self):
        if self._composite is None:
            image = QImage(
                self.OUTPUT_WIDTH, self.OUTPUT_HEIGHT, QImage.Format.Format_RGB888
            )
            image.fill(Qt.GlobalColor.black)
            if self._image is not None:
                painter = QPainter(image)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                painter.drawImage(self._rect, self._image)
                painter.end()
            self._composite = image
        return self._composite

    def frame_bgr(self):
        image = self.composed_image()
        rows = np.frombuffer(image.constBits(), np.uint8).reshape(
            image.height(), image.bytesPerLine()
        )
        rgb = rows[:, : image.width() * 3].reshape(image.height(), image.width(), 3)
        return np.ascontiguousarray(rgb[:, :, ::-1])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        view = self.viewport_rect()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(view, self.composed_image())
        painter.setPen(QPen(QColor("#666"), 1))
        painter.drawRect(view)
        if self._image is None:
            painter.setPen(QColor("#ddd"))
            painter.drawText(view, Qt.AlignmentFlag.AlignCenter, "No photo selected")
        else:
            # Editor handles are deliberately outside the composed camera frame.
            painter.setClipRect(view.adjusted(-6, -6, 6, 6))
            painter.setPen(QPen(QColor("#5a9dff"), 1, Qt.PenStyle.DashLine))
            painter.drawRect(self._screen_rect())
            painter.setPen(QPen(QColor("#5a9dff"), 1))
            painter.setBrush(QColor("white"))
            half = self.HANDLE_SIZE / 2
            for corner in self._corners():
                painter.drawRect(
                    QRectF(
                        corner.x() - half,
                        corner.y() - half,
                        self.HANDLE_SIZE,
                        self.HANDLE_SIZE,
                    )
                )
        painter.end()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self._image is None:
            return
        point = event.position()
        handle = self._handle_at(point)
        if handle is not None and self.viewport_rect().adjusted(
            -10, -10, 10, 10
        ).contains(point):
            self._gesture = (
                "resize",
                handle,
                QRectF(self._rect),
                self._to_output(point),
            )
        elif self.viewport_rect().contains(point) and self._screen_rect().contains(
            point
        ):
            self._gesture = ("move", None, QRectF(self._rect), self._to_output(point))
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            return
        event.accept()

    def mouseMoveEvent(self, event):
        if self._image is None:
            return
        point = event.position()
        if self._gesture is None:
            handle = self._handle_at(point)
            if handle is not None:
                cursor = (
                    Qt.CursorShape.SizeFDiagCursor
                    if handle % 2 == 0
                    else Qt.CursorShape.SizeBDiagCursor
                )
            else:
                cursor = (
                    Qt.CursorShape.OpenHandCursor
                    if self.viewport_rect().contains(point)
                    and self._screen_rect().contains(point)
                    else Qt.CursorShape.ArrowCursor
                )
            self.setCursor(cursor)
            return
        kind, handle, original, start = self._gesture
        delta = self._to_output(point) - start
        if kind == "move":
            self._rect = original.translated(delta)
        else:
            sx, sy = [(-1, -1), (1, -1), (1, 1), (-1, 1)][handle]
            # Project pointer movement onto the diagonal to preserve aspect ratio.
            factor = 1 + (
                delta.x() * sx * original.width() + delta.y() * sy * original.height()
            ) / (original.width() ** 2 + original.height() ** 2)
            factor = self._bounded_factor(factor, original)
            width, height = original.width() * factor, original.height() * factor
            anchor_x = original.right() if sx < 0 else original.left()
            anchor_y = original.bottom() if sy < 0 else original.top()
            self._rect = QRectF(
                anchor_x - width if sx < 0 else anchor_x,
                anchor_y - height if sy < 0 else anchor_y,
                width,
                height,
            )
        self._changed()
        event.accept()

    def _bounded_factor(self, factor, rect):
        fit = min(self.OUTPUT_WIDTH / rect.width(), self.OUTPUT_HEIGHT / rect.height())
        return max(fit * 0.05, min(fit * 8, factor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._gesture = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()

    def wheelEvent(self, event):
        if self._image is None or not self.viewport_rect().contains(event.position()):
            event.ignore()
            return
        steps = max(-10, min(10, event.angleDelta().y() / 120))
        factor = self._bounded_factor(1.12**steps, self._rect)
        anchor = self._to_output(event.position())
        if not self._rect.contains(anchor):
            anchor = self._rect.center()
        self._rect = QRectF(
            anchor.x() + (self._rect.x() - anchor.x()) * factor,
            anchor.y() + (self._rect.y() - anchor.y()) * factor,
            self._rect.width() * factor,
            self._rect.height() * factor,
        )
        self._changed()
        event.accept()
