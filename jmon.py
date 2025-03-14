import time
import asyncio
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor

def is_reachable(ip):
    """Check if the IP is reachable using a simple ping."""
    try:
        # Use subprocess to run ping command
        result = subprocess.run(
            f"ping -c 1 {ip}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Connection error for {ip}: {e}")
        return False

async def monitor_ip(ip, status, threshold_seconds):
    ip_id = hash(ip)  # Unique identifier for this IP context
    while True:
        try:
            reachable = is_reachable(ip)
            current_time = time.time()
            
            if reachable:
                logging.info(f"IP {ip} is up")
                status[ip]['last_up'] = current_time
                status[ip]['last_down_start'] = None
                status[ip]['alert_sent'] = False
            else:
                logging.warning(f"IP {ip} is down")
                
                if status[ip]['last_down_start'] is None:
                    status[ip]['last_down_start'] = current_time
                
                downtime = current_time - status[ip]['last_down_start']
                if downtime > threshold_seconds and not status[ip]['alert_sent']:
                    print(f"[{ip_id}] Alert: {ip} has been down for {(downtime//3600):.1f} hours")
                    status[ip]['alert_sent'] = True

        except Exception as e:
            print(f"Error monitoring {ip}: {e}")
        
        await asyncio.sleep(60)  # Poll every minute

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename='ip_monitor.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
