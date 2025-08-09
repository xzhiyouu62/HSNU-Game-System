from pwn import *
import time

HOST, PORT = 'skrctf.me', 3017

# 測試基本連接
def test_connection():
    try:
        print(f"[+] Attempting to connect to {HOST}:{PORT}")
        io = remote(HOST, PORT)
        print("[+] Connection successful!")
        
        # 接收初始數據
        print("[+] Receiving initial data...")
        data = io.recv(2048, timeout=5)
        print(f"[+] Received: {data.decode(errors='ignore')}")
        
        # 嘗試選項 3 (Print Flag)
        print("\n[+] Sending option 3...")
        io.sendline(b"3")
        
        # 接收響應
        response = io.recv(2048, timeout=5)
        print(f"[+] Response: {response.decode(errors='ignore')}")
        
        io.close()
        print("[+] Connection closed successfully")
        
    except Exception as e:
        print(f"[!] Error: {e}")
        if 'io' in locals():
            try:
                io.close()
            except:
                pass

if __name__ == "__main__":
    test_connection()
