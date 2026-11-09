import subprocess
import sys
import os

def main():
    print("================================================== - run.py:6")
    print("Poultry360  Smart Broiler Farm Management 🐔 - run.py:7")
    print("================================================== - run.py:8")
    
    print("[*] Upgrading pip and installing dependencies... - run.py:10")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print(f"[!] Error installing dependencies: {e} - run.py:15")
        sys.exit(1)
        
    print("[*] Launching Poultry360 Streamlit Application... - run.py:18")
    try:
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n[*] Poultry360 shut down successfully. Goodbye! - run.py:22")

if __name__ == "__main__":
    main()