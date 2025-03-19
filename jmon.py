import sys
import asyncio
import subprocess
from subprocess import TimeoutExpired
import argparse
from datetime import datetime, timedelta
import time

async def track_ip(ip, timeout_seconds, trackers, start_time):
    """Continuously monitor an IP and update its tracker state"""
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

    while True:
        await asyncio.sleep(1)  # Sleep for one second between checks
        is_down, downtime = await is_ip_down()  # Get the result
        
        if ip in trackers:
            tracker = trackers[ip]
        else:
            tracker = {
                'last_down_time': None,
                'current_downtime': 0.0
            }
            trackers[ip] = tracker

        if is_down:
            if tracker['last_down_time'] is None:
                tracker['last_down_time'] = datetime.now()
                tracker['current_downtime'] = downtime
            else:
                new_downtime = (datetime.now() - tracker['last_down_time']).total_seconds()
                tracker['current_downtime'] += new_downtime
                tracker['last_down_time'] = datetime.now()
        else:
            tracker['last_down_time'] = None
            tracker['current_downtime'] = 0.0

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
    
    # Initialize empty trackers dictionary
    ip_trackers = {}
    
    # Create tasks for each IP tracker and add to the event loop
    tasks = []
    for ip in args.ips:
        task = asyncio.create_task(track_ip(ip, args.timeout, ip_trackers, start_time))
        tasks.append(task)
    
    while True:
        # Check all trackers every second
        await asyncio.sleep(1)
        
        all_down = True
        for ip, tracker in ip_trackers.items():
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
            

if __name__ == "__main__":
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main(args))
        loop.close()
