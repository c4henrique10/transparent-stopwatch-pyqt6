import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

class TransparentStopwatch(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- TRANSPARENCY & ALWAYS ON TOP ---
        # Qt.WindowType.FramelessWindowHint: Removes the title bar and window boundaries.
        # Qt.WindowType.WindowStaysOnTopHint: Forces OS to render this window above all other applications.
        # Qt.WindowType.Tool: Removes the app from the taskbar and some window switchers for a cleaner look.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Qt.WidgetAttribute.WA_TranslucentBackground: Tells the compositor to make the widget's background completely transparent.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # --- OPACITY CONTROL ---
        self.current_opacity = 0.9
        self.setWindowOpacity(self.current_opacity)
        
        # Stopwatch logic variables
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.running = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        
        # Used for dragging the window
        self.old_pos = None 
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- TIME DISPLAY ---
        self.time_label = QLabel("00:00:00", self)
        
        # White digital-style font
        font = QFont("Consolas", 48, QFont.Weight.Bold)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet("color: white;")
        
        # Soft drop shadow to ensure readability on bright or white backgrounds
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 200)) # Dark semi-transparent shadow
        shadow.setOffset(2, 2)
        self.time_label.setGraphicsEffect(shadow)
        
        # --- MINIMAL BUTTON CONTROLS ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.reset_btn = QPushButton("Reset")
        
        # Small buttons with slight translucency
        btn_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 6px;
                padding: 6px 14px;
                font-family: Arial;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 180);
                border: 1px solid rgba(255, 255, 255, 180);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 80);
            }
        """
        for btn in (self.start_btn, self.pause_btn, self.reset_btn):
            btn.setStyleSheet(btn_style)
            btn_layout.addWidget(btn)
            
        self.start_btn.clicked.connect(self.start_timer)
        self.pause_btn.clicked.connect(self.pause_timer)
        self.reset_btn.clicked.connect(self.reset_timer)
        
        # --- OPACITY SETTINGS CONTROLS ---
        # Simple inline opacity layout
        opacity_layout = QHBoxLayout()
        self.opacity_down_btn = QPushButton("-")
        self.opacity_down_btn.setToolTip("Decrease Opacity (or Mouse Wheel Down)")
        self.opacity_up_btn = QPushButton("+")
        self.opacity_up_btn.setToolTip("Increase Opacity (or Mouse Wheel Up)")
        
        opacity_style = btn_style.replace("padding: 6px 14px;", "padding: 2px 8px;")
        self.opacity_down_btn.setStyleSheet(opacity_style)
        self.opacity_up_btn.setStyleSheet(opacity_style)
        self.opacity_down_btn.setFixedSize(26, 26)
        self.opacity_up_btn.setFixedSize(26, 26)
        
        self.opacity_down_btn.clicked.connect(lambda: self.adjust_opacity(-0.1))
        self.opacity_up_btn.clicked.connect(lambda: self.adjust_opacity(0.1))
        
        opacity_label = QLabel("Opacity:")
        opacity_label.setStyleSheet("color: rgba(255, 255, 255, 200); font-family: Arial; font-size: 11px; font-weight: bold;")
        
        # Small drop shadow for the opacity label as well
        lbl_shadow = QGraphicsDropShadowEffect()
        lbl_shadow.setBlurRadius(8)
        lbl_shadow.setColor(QColor(0, 0, 0, 200))
        lbl_shadow.setOffset(1, 1)
        opacity_label.setGraphicsEffect(lbl_shadow)

        opacity_layout.addStretch()
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_down_btn)
        opacity_layout.addWidget(self.opacity_up_btn)
        opacity_layout.addStretch()
        
        # Assemble main layout
        layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(btn_layout)
        layout.addLayout(opacity_layout)
        
        self.setLayout(layout)

    def format_time(self, t):
        # Calculate exactly how much time has passed
        minutes = int(t // 60)
        seconds = int(t % 60)
        milliseconds = int((t * 100) % 100)
        return f"{minutes:02d}:{seconds:02d}:{milliseconds:02d}"

    def update_time(self):
        # Real-time difference instead of relying purely on QTimer ticks for precision
        current_time = time.time()
        self.elapsed_time = current_time - self.start_time
        self.time_label.setText(self.format_time(self.elapsed_time))

    def start_timer(self):
        if not self.running:
            # Anchor the start time against already elapsed time to support pausing
            self.start_time = time.time() - self.elapsed_time
            self.timer.start(10) # 10ms poll rate for visually smooth millisecond updates
            self.running = True

    def pause_timer(self):
        if self.running:
            self.timer.stop()
            self.running = False

    def reset_timer(self):
        self.timer.stop()
        self.running = False
        self.elapsed_time = 0.0
        self.time_label.setText("00:00:00")

    # --- WINDOW DRAGGING IMPLEMENTATION ---
    # Overriding Qt mouse events provides a way to move a window without a title bar.
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Capture the global window coordinate mouse position on click
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            # Calculate how much the mouse has moved globally
            delta = event.globalPosition().toPoint() - self.old_pos
            # Re-position the window by that delta amount
            self.move(self.x() + delta.x(), self.y() + delta.y())
            # Update the old position to continue the drag seamlessly
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Stop dragging
            self.old_pos = None

    # --- OPACITY HOTKEYS & MOUSE WHEEL ---
    # Allows fast opacity manipulation using scroll wheel anywhere on the UI
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.adjust_opacity(0.05) # Scroll up
        else:
            self.adjust_opacity(-0.05) # Scroll down

    # Standard Keyboard inputs for +/- to adjust opacity
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.adjust_opacity(0.05)
        elif event.key() == Qt.Key.Key_Minus:
            self.adjust_opacity(-0.05)

    def adjust_opacity(self, delta):
        # Clip opacity bounds securely between 10% and 100%
        self.current_opacity = max(0.1, min(1.0, self.current_opacity + delta))
        self.setWindowOpacity(self.current_opacity)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TransparentStopwatch()
    window.resize(320, 180)
    window.show()
    sys.exit(app.exec())
