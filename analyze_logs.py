#!/usr/bin/env python3
"""
Virgin Media Hub Log Analyzer

Analyzes VM Hub event logs and generates comprehensive statistics and summaries.
"""

import json
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class VMHubLogAnalyzer:
    """Analyzer for Virgin Media Hub event logs."""
    
    # Error patterns for categorization
    T3_TIMEOUT_PATTERNS = [
        "T3 time-out",
        "16 consecutive T3 timeouts",
        "Unicast Maintenance Ranging",
        "No Ranging Response received"
    ]
    
    PRIORITY_LEVELS = ["critical", "error", "warning", "notice"]
    
    def __init__(self, log_file: str):
        """Initialize analyzer with log file path."""
        self.log_file = Path(log_file)
        self.events: List[Dict] = []
        self.stats: Dict = {}
        
    def load_logs(self) -> None:
        """Load and parse JSON log entries."""
        self.events = []
        
        with open(self.log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    event = json.loads(line)
                    # Parse timestamp
                    if 'time' in event:
                        event['datetime'] = datetime.fromisoformat(
                            event['time'].replace('Z', '+00:00')
                        )
                    self.events.append(event)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON at line {line_num}: {e}", 
                          file=sys.stderr)
                    
        print(f"Loaded {len(self.events)} events from {self.log_file}")
        
    def analyze(self) -> None:
        """Perform comprehensive analysis of log events."""
        if not self.events:
            print("No events to analyze. Load logs first.")
            return
            
        self.stats = {
            'total_events': len(self.events),
            'priority_counts': self._count_by_priority(),
            'date_range': self._get_date_range(),
            'critical_issues': self._analyze_critical_issues(),
            'error_issues': self._analyze_error_issues(),
            'warning_issues': self._analyze_warning_issues(),
            'message_types': self._analyze_message_types(),
            'outage_periods': self._identify_outage_periods(),
            'channel_failures': self._analyze_channel_failures(),
        }
        
    def _count_by_priority(self) -> Dict[str, int]:
        """Count events by priority level."""
        counts = Counter(event.get('priority', 'unknown') for event in self.events)
        return dict(counts)
        
    def _get_date_range(self) -> Tuple[str, str]:
        """Get the date range of logged events."""
        dates = [e['datetime'] for e in self.events if 'datetime' in e]
        if not dates:
            return ("N/A", "N/A")
        return (
            min(dates).strftime("%Y-%m-%d %H:%M:%S"),
            max(dates).strftime("%Y-%m-%d %H:%M:%S")
        )
        
    def _analyze_critical_issues(self) -> Dict:
        """Analyze critical priority events."""
        critical_events = [e for e in self.events if e.get('priority') == 'critical']
        
        # Categorize critical events
        t3_timeouts = []
        retries_exhausted = []
        consecutive_timeouts = []
        no_response = []
        
        for event in critical_events:
            msg = event.get('message', '')
            if '16 consecutive T3 timeouts' in msg:
                consecutive_timeouts.append(event)
            elif 'Retries exhausted' in msg:
                retries_exhausted.append(event)
            elif 'No Response received - T3 time-out' in msg or 'No Ranging Response received' in msg:
                no_response.append(event)
            elif 'T3 time-out' in msg:
                t3_timeouts.append(event)
                
        # Extract affected channels from consecutive timeout messages
        affected_channels = []
        for event in consecutive_timeouts:
            msg = event.get('message', '')
            if 'upstream channel' in msg:
                try:
                    channel = msg.split('upstream channel')[1].split(';')[0].strip()
                    affected_channels.append(channel)
                except:
                    pass
                    
        return {
            'total_count': len(critical_events),
            't3_timeout_starts': len(t3_timeouts),
            'retries_exhausted': len(retries_exhausted),
            'consecutive_timeouts': len(consecutive_timeouts),
            'no_response_events': len(no_response),
            'affected_upstream_channels': list(set(affected_channels)),
        }
        
    def _analyze_error_issues(self) -> Dict:
        """Analyze error priority events."""
        error_events = [e for e in self.events if e.get('priority') == 'error']
        
        # Categorize error messages
        message_types = Counter(event.get('message', '').split(';')[0] 
                               for event in error_events)
        
        return {
            'total_count': len(error_events),
            'message_types': dict(message_types),
        }
        
    def _analyze_warning_issues(self) -> Dict:
        """Analyze warning priority events."""
        warning_events = [e for e in self.events if e.get('priority') == 'warning']
        
        # Categorize warnings
        mdd_timeouts = [e for e in warning_events if 'MDD message timeout' in e.get('message', '')]
        dbc_mismatches = [e for e in warning_events if 'DBC-REQ Mismatch' in e.get('message', '')]
        
        return {
            'total_count': len(warning_events),
            'mdd_timeout_count': len(mdd_timeouts),
            'dbc_mismatch_count': len(dbc_mismatches),
        }
        
    def _analyze_message_types(self) -> Dict:
        """Analyze different types of status messages."""
        notice_events = [e for e in self.events if e.get('priority') == 'notice']
        
        cm_status = [e for e in notice_events if 'CM-STATUS' in e.get('message', '')]
        profile_changes = [e for e in notice_events if 'US profile assignment change' in e.get('message', '')]
        login_events = [e for e in notice_events if 'Login' in e.get('message', '')]
        
        return {
            'cm_status_messages': len(cm_status),
            'profile_changes': len(profile_changes),
            'login_events': len(login_events),
        }
        
    def _identify_outage_periods(self) -> List[Dict]:
        """Identify periods with multiple critical errors (potential outages)."""
        critical_events = [e for e in self.events 
                          if e.get('priority') == 'critical' and 'datetime' in e]
        
        if not critical_events:
            return []
            
        # Sort by time
        critical_events.sort(key=lambda x: x['datetime'])
        
        # Group events within 5 minutes of each other
        outages = []
        current_outage = [critical_events[0]]
        
        for event in critical_events[1:]:
            time_diff = (event['datetime'] - current_outage[-1]['datetime']).total_seconds()
            if time_diff <= 300:  # 5 minutes
                current_outage.append(event)
            else:
                if len(current_outage) >= 3:  # At least 3 critical events = outage
                    outages.append({
                        'start': current_outage[0]['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                        'end': current_outage[-1]['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                        'event_count': len(current_outage),
                        'duration_seconds': (current_outage[-1]['datetime'] - 
                                           current_outage[0]['datetime']).total_seconds()
                    })
                current_outage = [event]
                
        # Check last group
        if len(current_outage) >= 3:
            outages.append({
                'start': current_outage[0]['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                'end': current_outage[-1]['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                'event_count': len(current_outage),
                'duration_seconds': (current_outage[-1]['datetime'] - 
                                   current_outage[0]['datetime']).total_seconds()
            })
            
        return outages
        
    def _analyze_channel_failures(self) -> Dict:
        """Analyze which upstream channels experienced failures."""
        critical_events = [e for e in self.events if e.get('priority') == 'critical']
        
        channel_failures = defaultdict(int)
        
        for event in critical_events:
            msg = event.get('message', '')
            if 'upstream channel' in msg:
                try:
                    # Extract channel number
                    channel = msg.split('upstream channel')[1].split(';')[0].strip()
                    channel_failures[channel] += 1
                except:
                    pass
                    
        return dict(sorted(channel_failures.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999))
        
    def print_summary(self) -> None:
        """Print a formatted summary of the analysis."""
        if not self.stats:
            print("No statistics available. Run analyze() first.")
            return
            
        print("\n" + "="*70)
        print("VIRGIN MEDIA HUB LOG ANALYSIS SUMMARY")
        print("="*70)
        
        # Overview
        print(f"\n📊 OVERVIEW")
        print(f"  Total Events: {self.stats['total_events']:,}")
        print(f"  Date Range: {self.stats['date_range'][0]} to {self.stats['date_range'][1]}")
        
        # Priority breakdown
        print(f"\n📈 EVENT PRIORITY BREAKDOWN")
        priority_counts = self.stats['priority_counts']
        total = self.stats['total_events']
        for priority in ['critical', 'error', 'warning', 'notice']:
            count = priority_counts.get(priority, 0)
            percentage = (count / total * 100) if total > 0 else 0
            icon = {'critical': '🔴', 'error': '🟠', 'warning': '🟡', 'notice': '🔵'}.get(priority, '⚪')
            print(f"  {icon} {priority.capitalize():10} {count:6,} ({percentage:5.1f}%)")
            
        # Critical Issues
        crit = self.stats['critical_issues']
        print(f"\n🚨 CRITICAL ISSUES (T3 TIMEOUTS)")
        print(f"  Total Critical Events: {crit['total_count']}")
        print(f"  T3 Timeout Starts: {crit['t3_timeout_starts']}")
        print(f"  Retries Exhausted: {crit['retries_exhausted']}")
        print(f"  16 Consecutive Timeouts: {crit['consecutive_timeouts']}")
        print(f"  No Response Events: {crit['no_response_events']}")
        
        if crit['affected_upstream_channels']:
            channels = ', '.join(sorted(crit['affected_upstream_channels'], 
                                       key=lambda x: int(x) if x.isdigit() else 999))
            print(f"  Affected Upstream Channels: {channels}")
            
        # Channel Failures
        channel_failures = self.stats['channel_failures']
        if channel_failures:
            print(f"\n📡 UPSTREAM CHANNEL FAILURES")
            for channel, count in channel_failures.items():
                print(f"  Channel {channel:2}: {count:3} failures")
                
        # Error Issues
        err = self.stats['error_issues']
        if err['total_count'] > 0:
            print(f"\n⚠️  ERROR LEVEL ISSUES")
            print(f"  Total Error Events: {err['total_count']}")
            if err['message_types']:
                print(f"  Error Types:")
                for msg_type, count in err['message_types'].items():
                    print(f"    - {msg_type}: {count}")
                    
        # Warning Issues
        warn = self.stats['warning_issues']
        print(f"\n🟡 WARNING LEVEL ISSUES")
        print(f"  Total Warnings: {warn['total_count']}")
        print(f"  MDD Timeouts: {warn['mdd_timeout_count']}")
        print(f"  DBC Mismatches: {warn['dbc_mismatch_count']}")
        
        # Outage Periods
        outages = self.stats['outage_periods']
        if outages:
            print(f"\n⏱️  IDENTIFIED OUTAGE PERIODS ({len(outages)} total)")
            for i, outage in enumerate(outages[:10], 1):  # Show top 10
                duration_min = outage['duration_seconds'] / 60
                print(f"  {i}. {outage['start']} to {outage['end']}")
                print(f"     Duration: {duration_min:.1f} min | Events: {outage['event_count']}")
                
        # Status Messages
        msg_types = self.stats['message_types']
        print(f"\n📋 INFORMATIONAL EVENTS")
        print(f"  CM-STATUS Messages: {msg_types['cm_status_messages']}")
        print(f"  Profile Changes: {msg_types['profile_changes']}")
        print(f"  Login Events: {msg_types['login_events']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        if crit['total_count'] > 10:
            print(f"  ⚠️  URGENT: Severe upstream signal problems detected!")
            print(f"     - Contact Virgin Media technical support immediately")
            print(f"     - Check all cable connections for damage or looseness")
            print(f"     - Request upstream signal level testing")
            
        if warn['mdd_timeout_count'] > 20:
            print(f"  ⚠️  Frequent MDD timeouts indicate network communication issues")
            
        if warn['dbc_mismatch_count'] > 10:
            print(f"  ⚠️  DBC mismatches suggest signal quality problems")
            
        print("\n" + "="*70)
        
    def export_json(self, output_file: str = None) -> None:
        """Export statistics to JSON file."""
        if not self.stats:
            print("No statistics to export. Run analyze() first.")
            return
            
        if output_file is None:
            output_file = self.log_file.parent / f"{self.log_file.stem}_analysis.json"
            
        # Convert date_range tuple to dict for JSON serialization
        export_stats = self.stats.copy()
        export_stats['date_range'] = {
            'start': self.stats['date_range'][0],
            'end': self.stats['date_range'][1]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_stats, f, indent=2)
            
        print(f"\n✅ Statistics exported to: {output_file}")


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_logs.py <log_file> [--json]")
        print("\nExample:")
        print("  python analyze_logs.py vm_hub_events.log")
        print("  python analyze_logs.py vm_hub_events.log --json")
        sys.exit(1)
        
    log_file = sys.argv[1]
    export_json = '--json' in sys.argv or '-j' in sys.argv
    
    # Create analyzer
    analyzer = VMHubLogAnalyzer(log_file)
    
    # Load and analyze
    print(f"Loading log file: {log_file}")
    analyzer.load_logs()
    
    print("Analyzing events...")
    analyzer.analyze()
    
    # Print summary
    analyzer.print_summary()
    
    # Export JSON if requested
    if export_json:
        analyzer.export_json()
        

if __name__ == "__main__":
    main()
