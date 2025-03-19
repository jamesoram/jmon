import sys
import subprocess
from subprocess import TimeoutExpired
import argparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

def track_ip(ip, timeout_seconds):
    """Continuously monitor an IP and track its downtime"""
    last_down_start = None
    total_downtime = 0.0
    
    while True:
        is_down, downtime = is_ip_down(ip, timeout_seconds)
        
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
        try:
            yield {
                'ip': ip,
                'is_down': is_down,
                'total_downtime': total_downtime
            }
        except TimeoutExpired:
            end_time = datetime.now()
            downtime = (end_time - start_time).total_seconds()
            return True, downtime

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

def main(args):
    if not isinstance(args.timeout, float) or args.timeout <= 0:
        print("Error: Timeout must be a positive number")
        return
    
    # Initialize tracking for each IP
    ip_trackers = []
    
    with ThreadPoolExecutor() as executor:
        futures = []
        
        # Start continuous monitoring for each IP
        for ip in args.ips:
            future = executor.submit(track_ip, ip, args.timeout)
            futures.append(future)
            ip_trackers.append({'ip': ip, 'last_down_time': None, 'current_downtime': 0})
        
        while True:
            # Wait for updates from all trackers
            results = [f.result() for f in futures]
            
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
        main(args)
