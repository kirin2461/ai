"""Sci-Fi стили"""
SCIFI_STYLE = """
QMainWindow { background: #0a1628; }
QFrame#scifiPanel {
    background: rgba(10, 30, 50, 0.85);
    border: 1px solid rgba(0, 212, 255, 0.4);
    border-radius: 3px;
}
QPushButton {
    background: transparent;
    border: 2px solid #00d4ff;
    color: #00d4ff;
    padding: 12px 24px;
    font-weight: 600;
}
QPushButton:hover { background: rgba(0, 212, 255, 0.2); }
QLineEdit {
    background: rgba(0, 20, 40, 0.8);
    border: 1px solid rgba(0, 212, 255, 0.4);
    border-bottom: 2px solid #00d4ff;
    padding: 12px;
    color: #ffffff;
}
QTextEdit#chatArea {
    background: rgba(5, 15, 30, 0.9);
    border: 1px solid rgba(0, 212, 255, 0.3);
    color: #e0e0e0;
    padding: 15px;
}
QProgressBar {
    background: rgba(0, 50, 80, 0.5);
    border: 1px solid rgba(0, 212, 255, 0.3);
    height: 12px;
}
QProgressBar::chunk { background: #00d4ff; }
QLabel { color: #ffffff; }
QLabel#headerLabel { color: #00d4ff; font-weight: 700; text-transform: uppercase; }
"""
