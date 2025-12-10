#!/usr/bin/env python3
"""
Virgin Media Hub 5 Event Logger

Retrieves event logs from a Virgin Media Hub 5 router and stores them locally,
highlighting critical events in red.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import requests
import urllib3

# Suppress SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class VMHubLogger:
    """Logger for Virgin Media Hub 5 event logs."""
    
    # ANSI color codes
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, hub_ip: str, log_file: str, interval: int = 10):
        """
        Initialize the logger.
        
        Args:
            hub_ip: IP address of the Virgin Media Hub
            log_file: Path to the log file
            interval: Polling interval in seconds
        """
        self.hub_ip = hub_ip
        self.log_file = Path(log_file)
        self.interval = interval
        self.seen_events: Set[str] = set()
        
        # Create log file if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.touch(exist_ok=True)
        
        # Load existing events to avoid duplicates
        self._load_existing_events()
    
    def _load_existing_events(self):
        """Load existing events from the log file to avoid duplicates."""
        if self.log_file.exists() and self.log_file.stat().st_size > 0:
            try:
                with open(self.log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                event = json.loads(line.strip())
                                event_hash = self._hash_event(event)
                                self.seen_events.add(event_hash)
                            except json.JSONDecodeError:
                                continue
                print(f"Loaded {len(self.seen_events)} existing events from log file")
            except Exception as e:
                print(f"Warning: Could not load existing events: {e}")
    
    def _hash_event(self, event: Dict) -> str:
        """
        Create a unique hash for an event.
        
        Args:
            event: Event dictionary
            
        Returns:
            Hash string representing the event
        """
        # Use time, priority, and message to create a unique identifier
        return f"{event.get('time', '')}|{event.get('priority', '')}|{event.get('message', '')}"
    
    def _fetch_logs(self) -> List[Dict]:
        """
        Fetch logs from the Virgin Media Hub.
        
        Returns:
            List of event dictionaries
        """
        try:
            url = f"https://{self.hub_ip}/rest/v1/cablemodem/eventlog"
            response = requests.get(
                url,
                verify=False,  # Skip SSL verification (equivalent to curl -k)
                timeout=10
            )
            
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            events = data.get('eventlog', [])
            return events if isinstance(events, list) else []
                
        except requests.exceptions.Timeout:
            print("Timeout while fetching logs")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching logs: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching logs: {e}")
            return []
    
    def _format_critical_event(self, event: Dict) -> str:
        """
        Format a critical event for display.
        
        Args:
            event: Event dictionary
            
        Returns:
            Formatted string with ANSI color codes
        """
        time_str = event.get('time', 'Unknown time')
        message = event.get('message', 'No message')
        
        # Parse the time for better display
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            time_display = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            time_display = time_str
        
        return (
            f"{self.RED}{self.BOLD}🚨 CRITICAL EVENT{self.RESET}\n"
            f"{self.RED}Time: {time_display}{self.RESET}\n"
            f"{self.RED}Message: {message}{self.RESET}\n"
            f"{'-' * 80}"
        )
    
    def _save_event(self, event: Dict):
        """
        Save an event to the log file.
        
        Args:
            event: Event dictionary
        """
        with open(self.log_file, 'a') as f:
            json.dump(event, f)
            f.write('\n')
    
    def process_events(self, events: List[Dict]):
        """
        Process fetched events, saving new ones and highlighting critical ones.
        
        Args:
            events: List of event dictionaries
        """
        new_events = 0
        new_critical = 0
        
        # Sort events by time (oldest first) to maintain chronological order
        sorted_events = sorted(events, key=lambda e: e.get('time', ''))
        
        for event in sorted_events:
            event_hash = self._hash_event(event)
            
            # Skip if we've already seen this event
            if event_hash in self.seen_events:
                continue
            
            # New event - save it
            self.seen_events.add(event_hash)
            self._save_event(event)
            new_events += 1
            
            # If critical, display it
            if event.get('priority') == 'critical':
                print(self._format_critical_event(event))
                new_critical += 1
        
        if new_events > 0:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Processed {new_events} new event(s) ({new_critical} critical)")
    
    def run(self):
        """Run the logger continuously."""
        print(f"Starting VM Hub Logger")
        print(f"Hub IP: {self.hub_ip}")
        print(f"Log file: {self.log_file}")
        print(f"Polling interval: {self.interval} seconds")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                events = self._fetch_logs()
                if events:
                    self.process_events(events)
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping logger...")
            print(f"Total events logged: {len(self.seen_events)}")
            print(f"Log file: {self.log_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Virgin Media Hub 5 Event Logger - Continuously retrieves and logs event data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                                    # Use defaults
  %(prog)s --hub-ip 192.168.0.1               # Specify hub IP
  %(prog)s --interval 30                      # Poll every 30 seconds
  %(prog)s --log-file /var/log/vm_hub.log     # Custom log file location
        '''
    )
    
    parser.add_argument(
        '--hub-ip',
        default='192.168.0.1',
        help='IP address of the Virgin Media Hub (default: 192.168.0.1)'
    )
    
    parser.add_argument(
        '--log-file',
        default='vm_hub_events.log',
        help='Path to the log file (default: vm_hub_events.log)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Polling interval in seconds (default: 10)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='VM Hub Logger 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate interval
    if args.interval < 1:
        print("Error: Interval must be at least 1 second")
        sys.exit(1)
    
    # Create and run logger
    logger = VMHubLogger(args.hub_ip, args.log_file, args.interval)
    logger.run()


if __name__ == '__main__':
    main()
