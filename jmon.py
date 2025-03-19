import sys
import asyncio
import subprocess
from subprocess import TimeoutExpired
import argparse
from datetime import datetime, timedelta
import time

async def track_ip(ip, timeout_seconds, trackers, start_time):
    """Continuously monitor an IP and update its tracker state"""
    last_checked = None
    
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
        next_check_time = start_time + timedelta(seconds=timeout_seconds)
        while True:
            try:
                now = datetime.now()
                if last_checked is None or now >= next_check_time:
                    is_down, downtime = await is_ip_down()
                    last_checked = now
                    
                    # Update tracker with new downtime status
                    if ip in trackers:
                        tracker = trackers[ip]
                        if is_down:
                            if tracker['last_down_time'] is None:
                                tracker['last_down_time'] = now
                                tracker['current_downtime'] = downtime
                            else:
                                new_downtime = (now - tracker['last_down_time']).total_seconds()
                                tracker['current_downtime'] += new_downtime
                                tracker['last_down_time'] = now
                        else:
                            tracker['last_down_time'] = None
                            tracker['current_downtime'] = 0.0 if 'current_downtime' in tracker else downtime
                    else:
                        # Wait until the next scheduled check time
                        wait_time = next_check_time - now
                        if wait_time.total_seconds() > 0:
                            await asyncio.sleep(wait_time.total_seconds())
                        else:
                            await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
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
                # First time being down, set initial downtime
                tracker['last_down_time'] = datetime.now()
                tracker['current_downtime'] = downtime
            else:
                # Calculate new downtime and accumulate
                new_downtime = (datetime.now() - tracker['last_down_time']).total_seconds()
                tracker['current_downtime'] += new_downtime
                tracker['last_down_time'] = datetime.now()
        else:
            # IP is up, reset tracking
            tracker['last_down_time'] = None
            tracker['current_downtime'] = 0.0 if 'current_downtime' in tracker else downtime

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
    
    # Record the start time
    start_time = datetime.now()
    
    # Create tracking tasks and wait for them to complete
    track_tasks = [asyncio.create_task(track_ip(ip, args.timeout, ip_trackers, start_time)) 
                  for ip in args.ips]
    
    try:
        await asyncio.gather(*track_tasks)
    except KeyboardInterrupt:
        print("\nUser interrupted monitoring")
        return

    # Check if all IPs met the downtime threshold
    all_down = True
    for ip, tracker in ip_trackers.items():
        if tracker['last_down_time'] is None or \
           tracker['current_downtime'] < args.timeout:
            all_down = False
            break

    if all_down and len(ip_trackers) > 0:
        try:
            print("All IPs have been down for at least {} seconds, running command...".format(args.timeout))
            run_command(args.command)
            
            # Cancel tasks and wait for completion with exceptions
            for task in track_tasks:
                task.cancel()
            await asyncio.gather(*track_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
            

if __name__ == "__main__":
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main(args))
        loop.close()
