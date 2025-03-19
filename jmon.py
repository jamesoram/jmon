import sys
import asyncio
import subprocess
from subprocess import TimeoutExpired
import argparse
from datetime import datetime, timedelta
import time

async def track_ip(ip, timeout_seconds):
    """Continuously monitor an IP and track its downtime"""
    start_time = datetime.now()
    
    async def is_ip_down():
        try:
            # Use ping command with -c 1 to get quick response
            subprocess.check_output(f'ping -c 1 {ip}', shell=True, text=True)
            return False, None  # IP is up
        except subprocess.CalledProcessError as e:
            # If ping fails, record the time it was down
            end_time = datetime.now()
            downtime = (end_time - start_time).total_seconds()
            return True, downtime
            
    # Use the same start_time for both tracking and pinging

    last_down_start = None
    total_downtime = 0.0
    
    while True:
        is_down, downtime = is_ip_down()
        
        if is_down:
            # If the IP is down, start tracking downtime or continue existing downtime
            if last_down_start is None:
                last_down_start = datetime.now()
            else:
                # Extend the current downtime
                total_downtime += (datetime.now() - last_down_start).total_seconds()
                last_down_start = datetime.now()
        else:
            # IP is up, reset tracking
            last_down_start = None
            total_downtime = 0.0
        
        # Yield after each check to allow other threads to run
        await asyncio.sleep(1)  # Sleep for one second between checks
        return {
            'ip': ip,
            'is_down': is_down,
            'total_downtime': total_downtime
        }

def run_command(cmd):
    """Run the command in shell"""
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Command '{cmd}' executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")

# Create parser at top level since it's used in __main__
parser = argparse.ArgumentParser(description='''
 Monitor IP addresses and run a command when all are down for specified duration''')

parser.add_argument('--timeout', type=float, required=True,
                    help='Minimum downtime threshold in seconds')
parser.add_argument('--ips', nargs='+', required=True,
                    help='List of IP addresses to monitor (space-separated)')
parser.add_argument('--command', type=str, required=True,
                    help='Command to execute when all IPs are down')

async def main(args):
    if not isinstance(args.timeout, float) or args.timeout <= 0:
        print("Error: Timeout must be a positive number")
        return
    
    # Initialize tracking for each IP
    ip_trackers = []
    
    tasks = []
        
    # Create tasks for each IP tracker
    for ip in args.ips:
        tasks.append(track_ip(ip, args.timeout))
            ip_trackers.append({'ip': ip, 'last_down_time': None, 'current_downtime': 0})
        
        while True:
            # Wait for updates from all trackers
            results = await asyncio.gather(*tasks)
            
            # Update IP status and downtime tracking
            for i, result in enumerate(results):
                ip_info = ip_trackers[i]
                
                if result['is_down']:
                    if ip_info['last_down_time'] is None:
                        ip_info['last_down_time'] = datetime.now()
                        ip_info['current_downtime'] = 0.0
                    else:
                        downtime = (datetime.now() - ip_info['last_down_time']).total_seconds()
                        ip_info['current_downtime'] += downtime
                        ip_info['last_down_time'] = datetime.now()
                else:
                    ip_info['last_down_time'] = None
                    ip_info['current_downtime'] = 0.0
            
            # Check if all IPs have met the downtime threshold
            all_down = True
            for tracker in ip_trackers:
                if tracker['last_down_time'] is not None and \
                   tracker['current_downtime'] >= args.timeout:
                    continue
                else:
                    all_down = False
                    break
            
            if all_down:
                print("All IPs have been down for at least {} seconds, running command...".format(args.timeout))
                run_command(args.command)
                return  # Exit after executing the command
                
            time.sleep(1)  # Check again in one second
            
            # If we're checking an IP that's come back up, reset tracking

if __name__ == "__main__":
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main(args))
        loop.close()
