"""Точка входа AI Humanity"""
import sys
from PyQt6.QtWidgets import QApplication
from core.cognitive_cycle import CognitiveCycle
from gui.main_window_scifi import MainWindowSciFi
from config.settings import OPENAI_API_KEY

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    cognitive = CognitiveCycle(api_key=OPENAI_API_KEY if OPENAI_API_KEY else None)
    
    window = MainWindowSciFi(cognitive)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
