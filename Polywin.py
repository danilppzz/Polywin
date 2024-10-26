import sys
import ctypes
import socket
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QHBoxLayout, QWidget, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QTimer, QTime, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QFont, QIcon

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

def adjust_work_area(height):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    rect = RECT(0, height, screen_width, screen_height)
    ctypes.windll.user32.SystemParametersInfoW(0x002F, 0, ctypes.byref(rect), 0)

def restore_work_area():
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    rect = RECT(0, 0, screen_width, screen_height)
    ctypes.windll.user32.SystemParametersInfoW(0x002F, 0, ctypes.byref(rect), 0)

def get_local_ip():
    ip_address = None
    for iface in psutil.net_if_addrs():
        for addr in psutil.net_if_addrs()[iface]:
            if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                ip_address = addr.address
                break
        if ip_address:
            break
    return ip_address if ip_address else "IP not available"

def get_cpu_usage():
    return f"CPU {psutil.cpu_percent()}%"

def get_ram_usage():
    ram = psutil.virtual_memory()
    return f"RAM {ram.percent}%"

def get_current_time():
    return QTime.currentTime().toString("hh:mm:ss AP")

def is_fullscreen_window_active():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    rect = RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    return rect.left == 0 and rect.top == 0 and rect.right == screen_width and rect.bottom == screen_height

class CustomBar(QMainWindow):
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setGeometry(0, 0, 1920, self.size)
        self.setStyleSheet("background-color: #282c34;")
        self.hide()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("Polywin.png"))
        self.tray_icon.setVisible(True)

        tray_menu = QMenu()
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_application)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.showMessage("App Started", "The application is running", QSystemTrayIcon.Information)

        font = QFont('Segoe UI', self.size // 3)

        container = QWidget(self)
        layout = QHBoxLayout(container)

        data_left = [
            get_cpu_usage(),
            get_ram_usage()
        ]

        for text in data_left:
            label = QLabel(text)
            label.setStyleSheet("color: #bbc2cf; padding: 5px 8px; border-radius: 5px; margin: 0 5px;")
            label.setFont(font)
            layout.addWidget(label)

        layout.addStretch(1)

        ip_label = QLabel(f"{get_local_ip()}")
        ip_label.setStyleSheet("color: #bbc2cf; padding: 5px 8px; border-radius: 5px; margin: 0 5px;")
        ip_label.setFont(font)
        layout.addWidget(ip_label)

        time_label = QLabel(f"{get_current_time()}")
        time_label.setStyleSheet("color: #bbc2cf; padding: 5px 8px; border-radius: 5px; margin: 0 5px;")
        time_label.setFont(font)
        layout.addWidget(time_label)

        layout.setContentsMargins(10, 0, 10, 0)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)

        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_fullscreen)
        self.visibility_timer.start(1000)

        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)

    def update_info(self):
        for i, label in enumerate(self.findChildren(QLabel)):
            if i < 2:
                if i == 0:
                    label.setText(get_cpu_usage())
                elif i == 1:
                    label.setText(get_ram_usage())
        self.findChildren(QLabel)[2].setText(f"{get_local_ip()}")
        self.findChildren(QLabel)[3].setText(f"{get_current_time()}")

    def check_fullscreen(self):
        if is_fullscreen_window_active():
            self.fade_out()
        else:
            self.fade_in()

    def fade_out(self):
        if self.windowOpacity() != 0.0:
            self.animation.setStartValue(self.windowOpacity())
            self.animation.setEndValue(0.0)
            self.animation.start()

    def fade_in(self):
        if self.windowOpacity() != 1.0:
            self.animation.setStartValue(self.windowOpacity())
            self.animation.setEndValue(1.0)
            self.animation.start()

    def exit_application(self):
        restore_work_area()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

if __name__ == '__main__':
    size = 30
    adjust_work_area(height=size)

    app = QApplication(sys.argv)
    bar = CustomBar(size=size)
    bar.show()

    app.aboutToQuit.connect(restore_work_area)

    sys.exit(app.exec_())
