"""SpeedBoost overlay — transparent topmost animation.

Shows a column of green chevrons that animate sequentially during
clipboard dispatch, similar to the WPF SpeedboostOverlay.  The window
is frameless, transparent, always-on-top, and click-through.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from . import theme

CHEVRON_COUNT = 5
CHEVRON_CHAR = "❯"


class _Chevron(QLabel):
    """Single animated chevron with opacity support."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(CHEVRON_CHAR, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self._opacity = 0.15
        self._update_colour()

    # ── animated property ────────────────────────────────────────────

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float) -> None:
        self._opacity = value
        self._update_colour()

    opacity = Property(float, get_opacity, set_opacity)

    def _update_colour(self) -> None:
        alpha = max(0, min(255, int(self._opacity * 255)))
        self.setStyleSheet(f"color: rgba(76, 175, 80, {alpha}); background: transparent;")


class SpeedBoostOverlay(QWidget):
    """Transparent overlay with animated chevrons.

    Call ``start()`` to begin the animation and ``stop()`` to hide.
    Supports ``demo=True`` for a single play-through.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # frameless, transparent, topmost, click-through
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        # Windows: pass mouse clicks through
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)

        self.setFixedSize(60, CHEVRON_COUNT * 48 + 20)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)

        self._chevrons: list[_Chevron] = []
        for _ in range(CHEVRON_COUNT):
            chev = _Chevron(self)
            self._chevrons.append(chev)
            layout.addWidget(chev)

        self._group: QSequentialAnimationGroup | None = None
        self._demo = False

    # ── public ───────────────────────────────────────────────────────

    def start(self, *, demo: bool = False) -> None:
        """Show the overlay and begin the chevron cascade."""
        self._demo = demo
        self._position_bottom_right()
        self.show()
        self._animate()

    def stop(self) -> None:
        """Stop animation and hide."""
        if self._group:
            self._group.stop()
            self._group = None
        self.hide()

    # ── private ──────────────────────────────────────────────────────

    def _position_bottom_right(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.width() - 24
            y = geo.bottom() - self.height() - 24
            self.move(x, y)

    def _animate(self) -> None:
        if self._group:
            self._group.stop()

        self._group = QSequentialAnimationGroup(self)

        for chev in self._chevrons:
            anim = QPropertyAnimation(chev, b"opacity")
            anim.setDuration(280)
            anim.setStartValue(0.15)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self._group.addAnimation(anim)

        # fade all back down
        for chev in reversed(self._chevrons):
            anim = QPropertyAnimation(chev, b"opacity")
            anim.setDuration(200)
            anim.setStartValue(1.0)
            anim.setEndValue(0.15)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self._group.addAnimation(anim)

        if self._demo:
            self._group.finished.connect(self.stop)
        else:
            self._group.setLoopCount(-1)

        self._group.start()
