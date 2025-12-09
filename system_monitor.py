"""
System Monitor for Ollama Phi Model Load Testing
Tracks CPU, RAM usage during model execution
"""

import psutil
import time
import threading
from datetime import datetime
from typing import List, Dict, Any


class SystemMonitor:
    """Monitor system resources during Ollama execution"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics: List[Dict[str, Any]] = []
        self.monitor_thread = None
        self.interval = 0.5  # Sample every 0.5 seconds
        
    def start_monitoring(self):
        """Start monitoring system resources in background thread"""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("✓ System monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring and return collected metrics"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("✓ System monitoring stopped")
        return self.metrics
        
    def _monitor_loop(self):
        """Background loop to collect system metrics"""
        while self.monitoring:
            try:
                # Get memory info
                memory = psutil.virtual_memory()
                
                # Get CPU info
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
                
                # Record metrics
                metric = {
                    'timestamp': datetime.now(),
                    'ram_total_gb': memory.total / (1024**3),
                    'ram_used_gb': memory.used / (1024**3),
                    'ram_available_gb': memory.available / (1024**3),
                    'ram_percent': memory.percent,
                    'cpu_percent': cpu_percent,
                    'cpu_per_core': cpu_per_core,
                    'cpu_count': psutil.cpu_count()
                }
                
                self.metrics.append(metric)
                
            except Exception as e:
                print(f"Warning: Error collecting metrics: {e}")
                
            time.sleep(self.interval)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get static system information"""
        try:
            cpu_freq = psutil.cpu_freq()
            memory = psutil.virtual_memory()
            
            return {
                'cpu_model': self._get_cpu_model(),
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_threads': psutil.cpu_count(logical=True),
                'cpu_freq_mhz': cpu_freq.current if cpu_freq else 'N/A',
                'ram_total_gb': round(memory.total / (1024**3), 2),
                'platform': psutil.os.name
            }
        except Exception as e:
            print(f"Warning: Error getting system info: {e}")
            return {}
    
    def _get_cpu_model(self) -> str:
        """Get CPU model name (Windows-specific)"""
        try:
            import platform
            return platform.processor()
        except:
            return "Unknown CPU"


class IterationMetrics:
    """Track metrics for each iteration"""
    
    def __init__(self):
        self.iterations: List[Dict[str, Any]] = []
        
    def add_iteration(self, iteration_num: int, execution_time: float, 
                     peak_ram: float, avg_cpu: float, response_length: int):
        """Add metrics for a completed iteration"""
        self.iterations.append({
            'iteration': iteration_num,
            'execution_time': execution_time,
            'peak_ram_gb': peak_ram,
            'avg_cpu_percent': avg_cpu,
            'response_length': response_length,
            'timestamp': datetime.now()
        })
        
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate aggregate statistics"""
        if not self.iterations:
            return {}
            
        exec_times = [i['execution_time'] for i in self.iterations]
        ram_peaks = [i['peak_ram_gb'] for i in self.iterations]
        cpu_avgs = [i['avg_cpu_percent'] for i in self.iterations]
        
        import statistics
        
        return {
            'total_iterations': len(self.iterations),
            'avg_execution_time': statistics.mean(exec_times),
            'min_execution_time': min(exec_times),
            'max_execution_time': max(exec_times),
            'stddev_execution_time': statistics.stdev(exec_times) if len(exec_times) > 1 else 0,
            'avg_ram_peak': statistics.mean(ram_peaks),
            'max_ram_peak': max(ram_peaks),
            'avg_cpu': statistics.mean(cpu_avgs),
            'max_cpu': max(cpu_avgs)
        }
