#!/usr/bin/env python3
"""
Performance monitoring script for Mangaku API
"""

import requests
import time
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List
import statistics

class APIMonitor:
    """Monitor API performance and health."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.metrics = {
            'response_times': [],
            'status_codes': {},
            'error_count': 0,
            'success_count': 0
        }
    
    def check_health(self) -> Dict:
        """Check API health status."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': duration,
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None,
                'status_code': None
            }
    
    def test_endpoint(self, endpoint: str, params: Dict = None) -> Dict:
        """Test a specific endpoint and measure performance."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = self.session.get(url, params=params, timeout=30)
            duration = time.time() - start_time
            
            # Update metrics
            self.metrics['response_times'].append(duration)
            status_code = response.status_code
            self.metrics['status_codes'][status_code] = self.metrics['status_codes'].get(status_code, 0) + 1
            
            if 200 <= status_code < 300:
                self.metrics['success_count'] += 1
            else:
                self.metrics['error_count'] += 1
            
            return {
                'endpoint': endpoint,
                'status_code': status_code,
                'response_time': duration,
                'response_size': len(response.content) if response.content else 0,
                'success': 200 <= status_code < 300,
                'headers': dict(response.headers),
                'data_preview': str(response.text)[:200] if response.text else None
            }
            
        except Exception as e:
            self.metrics['error_count'] += 1
            return {
                'endpoint': endpoint,
                'error': str(e),
                'success': False,
                'response_time': None
            }
    
    def load_test(self, endpoints: List[Dict], duration: int = 60, concurrent: int = 1):
        """Run load test on specified endpoints."""
        print(f"🚀 Starting load test for {duration} seconds...")
        print(f"📊 Testing {len(endpoints)} endpoints with {concurrent} concurrent requests")
        
        start_time = time.time()
        results = []
        
        while time.time() - start_time < duration:
            for endpoint_config in endpoints:
                endpoint = endpoint_config['endpoint']
                params = endpoint_config.get('params', {})
                
                result = self.test_endpoint(endpoint, params)
                results.append(result)
                
                # Rate limiting - small delay between requests
                time.sleep(0.1)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate performance report."""
        if not self.metrics['response_times']:
            return "❌ No data collected"
        
        response_times = self.metrics['response_times']
        
        report = [
            "=" * 60,
            "📊 MANGAKU API PERFORMANCE REPORT",
            "=" * 60,
            f"⏱️  Test Duration: {len(results)} requests",
            f"✅ Success Rate: {self.metrics['success_count']}/{len(results)} ({(self.metrics['success_count']/len(results)*100):.1f}%)",
            f"❌ Error Rate: {self.metrics['error_count']}/{len(results)} ({(self.metrics['error_count']/len(results)*100):.1f}%)",
            "",
            "📈 RESPONSE TIME STATISTICS:",
            f"   • Average: {statistics.mean(response_times):.3f}s",
            f"   • Median: {statistics.median(response_times):.3f}s",
            f"   • Min: {min(response_times):.3f}s",
            f"   • Max: {max(response_times):.3f}s",
            f"   • 95th Percentile: {self._percentile(response_times, 95):.3f}s",
            "",
            "📊 STATUS CODE DISTRIBUTION:"
        ]
        
        for status_code, count in sorted(self.metrics['status_codes'].items()):
            percentage = (count / len(results)) * 100
            report.append(f"   • {status_code}: {count} ({percentage:.1f}%)")
        
        report.extend([
            "",
            "🔍 PERFORMANCE ANALYSIS:",
            self._analyze_performance(response_times),
            "",
            "⚡ OPTIMIZATION RECOMMENDATIONS:",
            self._get_recommendations(response_times, self.metrics)
        ])
        
        return "\n".join(report)
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of response times."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _analyze_performance(self, response_times: List[float]) -> str:
        """Analyze performance and provide insights."""
        avg_time = statistics.mean(response_times)
        
        if avg_time < 0.5:
            return "🟢 Excellent - Response times are very fast"
        elif avg_time < 1.0:
            return "🟡 Good - Response times are acceptable"
        elif avg_time < 2.0:
            return "🟠 Fair - Response times could be improved"
        else:
            return "🔴 Poor - Response times need optimization"
    
    def _get_recommendations(self, response_times: List[float], metrics: Dict) -> str:
        """Generate optimization recommendations."""
        recommendations = []
        avg_time = statistics.mean(response_times)
        error_rate = metrics['error_count'] / (metrics['success_count'] + metrics['error_count'])
        
        if avg_time > 1.0:
            recommendations.append("• Consider implementing more aggressive caching")
            recommendations.append("• Optimize database queries and scraping logic")
        
        if error_rate > 0.1:
            recommendations.append("• Investigate error causes and improve error handling")
            recommendations.append("• Consider implementing circuit breakers")
        
        if max(response_times) > 5.0:
            recommendations.append("• Implement request timeouts and retries")
            recommendations.append("• Consider async processing for heavy operations")
        
        if not recommendations:
            recommendations.append("• Performance looks good! Monitor regularly")
        
        return "\n".join(recommendations)
    
    def monitor_realtime(self, interval: int = 30):
        """Monitor API in real-time."""
        print("🔄 Starting real-time monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                health = self.check_health()
                
                status_emoji = "🟢" if health['status'] == 'healthy' else "🔴"
                print(f"[{timestamp}] {status_emoji} Health: {health['status']}")
                
                if health['response_time']:
                    print(f"                Response Time: {health['response_time']:.3f}s")
                
                if health.get('data'):
                    cache_status = health['data'].get('cache_status', 'unknown')
                    rate_limit_status = health['data'].get('rate_limit_status', 'unknown')
                    print(f"                Cache: {cache_status}, Rate Limit: {rate_limit_status}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description="Monitor Mangaku API performance")
    parser.add_argument('--url', default='http://localhost:5000', help='API base URL')
    parser.add_argument('--mode', choices=['health', 'load', 'monitor'], default='health',
                       help='Monitoring mode')
    parser.add_argument('--duration', type=int, default=60, help='Load test duration in seconds')
    parser.add_argument('--interval', type=int, default=30, help='Real-time monitoring interval')
    
    args = parser.parse_args()
    
    monitor = APIMonitor(args.url)
    
    if args.mode == 'health':
        print("🏥 Checking API Health...")
        health = monitor.check_health()
        print(json.dumps(health, indent=2))
        
        if health['status'] != 'healthy':
            sys.exit(1)
    
    elif args.mode == 'load':
        endpoints = [
            {'endpoint': '/manga', 'params': {'page': 1}},
            {'endpoint': '/manga', 'params': {'page': 2}},
            {'endpoint': '/health'},
        ]
        
        results = monitor.load_test(endpoints, args.duration)
        report = monitor.generate_report(results)
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_report_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {filename}")
    
    elif args.mode == 'monitor':
        monitor.monitor_realtime(args.interval)

if __name__ == '__main__':
    main() 