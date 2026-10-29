"""Stream a selected still image through Camera11, without opening a webcam."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QStandardPaths, QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.virtual_camera import CAMERA_NAME, VirtualCamera
from modules.photo_canvas import PhotoCanvas


class PhotoStreamPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera = None
        self._frame = None
        self._directory = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QLabel("Choose a photo and stream it through Camera 11.")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        self.preview = PhotoCanvas()
        self._edit_timer = QTimer(self)
        self._edit_timer.setSingleShot(True)
        self._edit_timer.setInterval(33)
        self._edit_timer.timeout.connect(self._publish_composition)
        self.preview.compositionChanged.connect(self._composition_changed)
        layout.addWidget(self.preview, 1)
        self.filename = QLabel("")
        self.filename.setWordWrap(True)
        layout.addWidget(self.filename)
        self.select_button = QPushButton("Select image from gallery")
        self.select_button.clicked.connect(self.choose_image)
        layout.addWidget(self.select_button)
        hint = QLabel(
            "Drag the photo to move it. Drag a corner or use the mouse wheel to resize. Uncovered areas stay black."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.reset_button = QPushButton("Fit / Center image")
        self.reset_button.setObjectName("secondary")
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(self.preview.reset_fit)
        layout.addWidget(self.reset_button)
        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start streaming")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_stream)
        buttons.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop streaming")
        self.stop_button.setObjectName("danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_stream)
        buttons.addWidget(self.stop_button)
        layout.addLayout(buttons)
        destination = QLabel(f"Select this camera in your calling app:\n{CAMERA_NAME}")
        destination.setWordWrap(True)
        destination.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(destination)
        self.status = QLabel("Select an image to begin.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self._health_timer = QTimer(self)
        self._health_timer.setInterval(500)
        self._health_timer.timeout.connect(self._check_stream)

    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select a photo",
            self._directory,
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)",
        )
        if path:
            self.load_image(path)

    def load_image(self, path):
        try:
            with Image.open(path) as source:
                oriented = ImageOps.exif_transpose(source)
                # Transparent images are composited on the stream's black background.
                rgba = oriented.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
                rgb = np.array(Image.alpha_composite(background, rgba).convert("RGB"))
            frame = np.ascontiguousarray(rgb[:, :, ::-1])
            height, width = rgb.shape[:2]
            image = QImage(
                rgb.data,
                width,
                height,
                rgb.strides[0],
                QImage.Format.Format_RGB888,
            ).copy()
        except Exception as exc:
            self.status.setText(f"Could not open that image: {exc}")
            return False
        self._frame = frame
        self.preview.set_image(image)
        self._edit_timer.stop()
        delivered = self._publish_composition()
        self._directory = str(Path(path).parent)
        self.filename.setTextFormat(Qt.TextFormat.PlainText)
        self.filename.setText(Path(path).name)
        self.filename.setToolTip(str(path))
        self._update_buttons()
        if delivered:
            self.status.setText(
                "Streaming photo to Camera 11."
                if self._camera
                else "Photo ready. Click Start streaming."
            )
        return True

    def start_stream(self):
        if self._frame is None or self._camera is not None:
            return
        try:
            self._camera = VirtualCamera()
            self._camera.send(self.preview.frame_bgr())
        except Exception as exc:
            self._stream_failed(exc)
            return
        self._health_timer.start()
        self._update_buttons()
        self.status.setText("Streaming photo to Camera 11. Keep this application open.")

    def stop_stream(self):
        self._edit_timer.stop()
        self._health_timer.stop()
        if self._camera is not None:
            self._camera.close()
            self._camera = None
            self.status.setText("Stream stopped.")
        self._update_buttons()

    def _stream_failed(self, error):
        self.stop_stream()
        self.status.setText(f"Could not stream to Camera 11: {error}")

    def _check_stream(self):
        if self._camera is not None and self._camera.error:
            self._stream_failed(self._camera.error)

    def _update_buttons(self):
        self.start_button.setEnabled(self._frame is not None and self._camera is None)
        self.stop_button.setEnabled(self._camera is not None)
        self.reset_button.setEnabled(self._frame is not None)

    def _composition_changed(self):
        if self._camera is not None and not self._edit_timer.isActive():
            self._edit_timer.start()

    def _publish_composition(self):
        if self._camera is not None:
            try:
                self._camera.send(self.preview.frame_bgr())
            except Exception as exc:
                self._stream_failed(exc)
                return False
        return True

    def closeEvent(self, event):
        self.stop_stream()
        super().closeEvent(event)
