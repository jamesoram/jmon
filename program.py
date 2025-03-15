import sys
import subprocess
import argparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

def is_ip_down(ip, timeout_seconds):
    """Check if an IP is down using ping"""
    start_time = datetime.now()
    
    try:
        # Use ping command with -c 1 to get quick response
        subprocess.check_output(f'ping -c 1 {ip}', shell=True, text=True)
        return False, None  # IP is up
    except subprocess.CalledProcessError as e:
        # If ping fails, record the time it was down
        end_time = datetime.now()
        downtime = (end_time - start_time).total_seconds()
        return True, downtime
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

def main():
    parser = argparse.ArgumentParser(description='Monitor IP addresses and run command on downtime')
    parser.add_argument('-c', '--command', required=True, help='Command to run when IPs are down')
    parser.add_argument('-i', '--ips', required=True, nargs='+',
                        help='IP addresses to monitor (repeat for multiple)')
    parser.add_argument('-t', '--timeout', type=float, required=True,
                        help='Timeout period in seconds before triggering command')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not isinstance(args.timeout, float) or args.timeout <= 0:
        print("Error: Timeout must be a positive number")
        return
    
    # Monitor IPs and their downtime
    with ThreadPoolExecutor() as executor:
        futures = []
        for ip in args.ips:
            future = executor.submit(is_ip_down, ip, args.timeout)
            futures.append(future)
        
        # Wait for all pings to complete
        results = [f.result() for f in futures]
        
        # Check if all IPs are down beyond the timeout
        all_down = True
        total_downtime = 0.0
        
        for is_down, downtime in results:
            if not is_down:
                all_down = False
                break
            total_downtime += downtime
        
        if all_down and total_downtime >= args.timeout:
            print("All IPs are down, running command...")
            run_command(args.command)
        else:
            print("Some or all IPs are still up, no action taken.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        main()
