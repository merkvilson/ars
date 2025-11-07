import socket

def get_local_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip

# if __name__ == "__main__":
#     print("Your local IP address is:", get_local_ip())



import subprocess

# Command to run ComfyUI
cmd = r'.\python_embeded\python.exe -s ComfyUI\main.py --cpu --windows-standalone-build --listen 0.0.0.0 --port 8188'

# Run it
subprocess.run(cmd, shell=True)

# Optional: Wait for user input before closing (similar to "pause")
input("Press Enter to exit...")
