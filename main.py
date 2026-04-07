import sys
from PyQt6.QtWidgets import QApplication

# 唯一的切入点，调用放在 gui 外壳中的窗口对象
from gui.main_window import MainWindow

def main():
    print("[MSP_System] 启动应用程序核心...")
    app = QApplication(sys.argv)
    
    # 强制整个应用程序采用 Fusion 主题，外观更专业
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.resize(1100, 750)
    window.show()
    
    # 进入安全退出循环机制
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
