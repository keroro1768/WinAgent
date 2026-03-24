"""
WinAgent UIA Demo 使用 pywinauto (更穩定)
"""

import time
from datetime import datetime

from pywinauto import Application, timings

# 設定等待時間
timings.wait_until_passes_timeout = 5

def demo():
    print("=" * 50)
    print("WinAgent UIA Demo (pywinauto)")
    print("=" * 50)
    
    try:
        # 1. 啟動 Notepad
        print("\n[1] 啟動 Notepad...")
        app = Application(backend="win32").start("notepad.exe")
        time.sleep(1)
        
        # 取得主視窗
        dlg = app.window(title_re=".*Notepad.*")
        print(f"    [OK] 視窗已啟動")
        
        # 2. 輸入文字
        print("\n[2] 輸入文字...")
        # 找到文字編輯區
        edit = dlg.Edit
        edit.set_edit_text(f"Hi, I win - {datetime.now().strftime('%Y/%m/%d %H:%M')}")
        print("    [OK] 文字已輸入")
        
        # 3. 存檔 (使用選單)
        print("\n[3] 存檔...")
        # 點擊 檔案 -> 另存新檔
        dlg.menu_select("檔案->另存新檔")
        time.sleep(0.5)
        
        # 4. 處理存檔對話框
        print("\n[4] 處理存檔對話框...")
        
        # 等待存檔對話框
        save_dlg = app.window(title_re=".*另存.*")
        if not save_dlg:
            save_dlg = app.window(title_re=".*Save.*")
        
        # 輸入檔名
        fname = f"WinTest_{datetime.now().strftime('%H%M%S')}.txt"
        save_dlg.Edit.set_edit_text(fname)
        print(f"    檔名: {fname}")
        
        # 點擊儲存
        save_dlg.Button.click()
        time.sleep(0.5)
        
        # 5. 檢查結果
        print("\n[5] 檢查結果...")
        import os
        docs = os.path.expanduser("~/Documents")
        fpath = os.path.join(docs, fname)
        
        print("\n" + "=" * 50)
        if os.path.exists(fpath):
            print(f"[OK] 已存檔: {fpath}")
            with open(fpath, 'r', encoding='utf-8') as f:
                print("\n內容:")
                print("-" * 20)
                print(f.read())
        else:
            # 嘗試桌面
            desktop = os.path.expanduser("~/Desktop")
            fpath = os.path.join(desktop, fname)
            if os.path.exists(fpath):
                print(f"[OK] 已存檔: {fpath}")
            else:
                print("[WARN] 找不到檔案")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[錯誤] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 關閉
        print("\n[清理] 關閉 Notepad...")
        try:
            app.kill()
        except:
            pass
        print("[完成]")

if __name__ == "__main__":
    demo()