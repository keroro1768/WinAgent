import subprocess
import time
import sys
import os

try:
    import uiautomation as auto
except ImportError:
    print("正在安裝 uiautomation 庫...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

def spy_app(app_path):
    print(f"[*] 正在啟動應用程式: {app_path}")
    # 1. 用 CLI 啟動應用程式
    proc = subprocess.Popen(app_path)
    time.sleep(2)  # 等待視窗出現

    # 2. 取得視窗對象
    # 根據 PID 尋找視窗
    window = auto.WindowControl(searchDepth=1, ProcessId=proc.pid)
    
    if not window.Exists(0):
        print("[!] 找不到應用程式視窗。")
        return

    print(f"[+] 成功連線到視窗: {window.Name} (PID: {proc.pid})")
    print(f"[*] 執行狀態: 執行中 (Running)")
    print("-" * 50)

    # 3. 遍歷 UI 控制項並找出按鈕
    print("[*] 正在掃描所有可點擊按鈕...")
    buttons = []
    
    # 遞迴遍歷所有控制項
    def walk(control, depth):
        # 判斷是否為按鈕 (ControlType 4 為 Button)
        if control.ControlType == auto.ControlType.ButtonControl:
            # 檢查是否可點擊 (通常有 Name 且 Enabled)
            name = control.Name or "(未命名)"
            buttons.append(name)
            
        for child in control.GetChildren():
            walk(child, depth + 1)

    walk(window, 0)

    if buttons:
        print(f"[V] 發現 {len(buttons)} 個可點擊按鈕:")
        for btn in buttons:
            print(f"    - {btn}")
    else:
        print("[?] 未發現明確的按鈕控制項。")

    # 4. 保持開啟一段時間後關閉 (或由使用者決定)
    print("-" * 50)
    print("[*] 示範結束，正在關閉應用程式...")
    proc.terminate()

if __name__ == "__main__":
    # 預設啟動記事本進行測試
    target = "notepad.exe"
    spy_app(target)
