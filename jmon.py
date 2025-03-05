import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

def is_reachable(ip):
    """Check if the IP is reachable using a simple ping."""
    try:
        # This is a simplified check; in real scenarios, use appropriate libraries.
        return True  # Replace with actual connectivity check logic
    except Exception as e:
        print(f"Connection error for {ip}: {e}")
        return False

async def monitor_ip(ip, status, threshold_seconds):
    while True:
        try:
            if is_reachable(ip):
                status[ip]['last_up'] = time.time()
                status[ip]['last_down_start'] = None
                status[ip]['alert_sent'] = False
            else:
                if status[ip]['last_down_start'] is None:
                    status[ip]['last_down_start'] = time.time()
                
                downtime = time.time() - status[ip]['last_down_start']
                if downtime > threshold_seconds and not status[ip]['alert_sent']:
                    print(f"Alert: {ip} has been down for {downtime//3600} hours")
                    status[ip]['alert_sent'] = True

        except Exception as e:
            print(f"Error monitoring {ip}: {e}")
        
        await asyncio.sleep(60)  # Poll every minute

async def main():
    ips = ['192.168.1.1', '192.168.1.2']  # Example IPs
    X_hours = 24  # Threshold in hours
    threshold_seconds = X_hours * 3600
    status = {ip: {'last_up': time.time(), 
                  'last_down_start': None, 
                  'alert_sent': False} for ip in ips}
    
    # Use a ThreadPoolExecutor to handle concurrent IP checks
    executor = ThreadPoolExecutor(max_workers=len(ips))
    
    tasks = []
    for ip in ips:
        task = asyncio.create_task(monitor_ip(ip, status, threshold_seconds))
        tasks.append(task)
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
