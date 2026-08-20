import os
import psutil

# Print header format
print(f"{'PID':<8} {'Name':<25} {'Status':<10}")
print("-" * 45)

def IsProcessActive(process_name: str) -> dict:
    my_pid = os.getpid()
    if not process_name:
        return {'status': 'error', 'message': 'Process name is required!'}
    for process in psutil.process_iter(['pid', 'name', 'status']):
        try:
            if process_name in process.info['name'] and my_pid != process.info['pid']:
                return {'status' : 'error', 'message': 'Process is already active!'}
        except Exception as ex:
            return {'status': 'error', 'message': {str(ex)}}
    return {'status': 'ok', 'message': 'Ok to start process!'}

def DisplayActiveProcesses(filter_str: str = None):
    processes = psutil.process_iter()
    # Iterate over all running processes
    for process in psutil.process_iter(['pid', 'name', 'status']):
        try:
            # Access process information as a dictionary
            info = process.info
            if not filter_str:
                print(f"{info['pid']:<8} {info['name']:<25} {info['status']:<10}")
            elif filter_str.lower() in info['name'].lower():
                print(f"{info['pid']:<8} {info['name']:<25} {info['status']:<10}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Ignore processes that terminated or restrict access during iteration
            pass