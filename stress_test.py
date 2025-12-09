"""
High-Load Stress Test for Ollama Models
Runs concurrent requests to push system to its limits
"""

import sys
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from system_monitor import SystemMonitor, IterationMetrics
from ollama_client import OllamaClient
from generate_report import ReportGenerator
import queue


class ConcurrentLoadTester:
    """Orchestrate concurrent load testing of Ollama models"""
    
    def __init__(self, model: str = "llama3", total_requests: int = 50, 
                 concurrent_requests: int = 5,
                 prompt: str = "Explain quantum computing in simple terms"):
        self.model = model
        self.total_requests = total_requests
        self.concurrent_requests = concurrent_requests
        self.prompt = prompt
        self.ollama = OllamaClient()
        self.monitor = SystemMonitor()
        self.iter_metrics = IterationMetrics()
        self.completed_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        
    def _execute_single_request(self, request_num: int) -> dict:
        """Execute a single request and return results"""
        import psutil
        
        # Track peak CPU during execution
        cpu_samples = []
        monitoring = {'active': True}
        
        def monitor_cpu():
            """Background thread to continuously monitor CPU"""
            while monitoring['active']:
                cpu_samples.append(psutil.cpu_percent(interval=0.1))
                time.sleep(0.1)
        
        # Get baseline metrics
        baseline_ram = psutil.virtual_memory().used / (1024**3)
        
        # Start CPU monitoring thread
        cpu_thread = threading.Thread(target=monitor_cpu, daemon=True)
        cpu_thread.start()
        
        # Execute model
        result = self.ollama.generate(self.model, self.prompt)
        
        # Stop CPU monitoring
        monitoring['active'] = False
        cpu_thread.join(timeout=1)
        
        # Get peak metrics
        peak_ram = psutil.virtual_memory().used / (1024**3)
        peak_cpu = max(cpu_samples) if cpu_samples else 0.0
        
        return {
            'request_num': request_num,
            'success': result['success'],
            'execution_time': result['execution_time'],
            'response_length': len(result['response']) if result['success'] else 0,
            'peak_ram': peak_ram,
            'peak_cpu': peak_cpu,
            'error': result.get('error')
        }
    
    def run(self):
        """Execute the concurrent load test"""
        print("=" * 70)
        print("🔥 OLLAMA HIGH-LOAD STRESS TEST 🔥")
        print("=" * 70)
        print(f"\n📋 Configuration:")
        print(f"   Model: {self.model}")
        print(f"   Total Requests: {self.total_requests}")
        print(f"   Concurrent Requests: {self.concurrent_requests}")
        print(f"   Prompt: {self.prompt[:50]}...")
        print()
        
        # Check Ollama connection
        print("🔍 Checking Ollama connection...")
        if not self.ollama.check_connection():
            print("\n❌ ERROR: Cannot connect to Ollama!")
            print("   Please ensure Ollama is running (http://localhost:11434)")
            print("   You can start it with: ollama serve")
            return False
        
        print("✓ Ollama is running")
        
        # Verify model
        print(f"\n🔍 Verifying model '{self.model}'...")
        available_models = self.ollama.list_models()
        
        if available_models and self.model not in available_models:
            print(f"\n⚠ Warning: Model '{self.model}' not found. Available models:")
            for m in available_models[:10]:
                print(f"   - {m}")
            print(f"\n   Attempting to use '{self.model}' anyway...")
        else:
            print(f"✓ Model '{self.model}' is available")
        
        # Get system info
        system_info = self.monitor.get_system_info()
        print(f"\n💻 System Information:")
        print(f"   CPU: {system_info.get('cpu_model', 'N/A')}")
        print(f"   Cores: {system_info.get('cpu_count', 'N/A')} ({system_info.get('cpu_threads', 'N/A')} threads)")
        print(f"   RAM: {system_info.get('ram_total_gb', 'N/A')} GB")
        
        # Start monitoring
        print(f"\n{'=' * 70}")
        print("🏁 STARTING HIGH-LOAD STRESS TEST")
        print(f"{'=' * 70}\n")
        
        self.monitor.start_monitoring()
        test_start_time = time.time()
        
        # Execute concurrent requests
        print(f"⚡ Running {self.total_requests} requests with {self.concurrent_requests} concurrent workers...\n")
        
        with ThreadPoolExecutor(max_workers=self.concurrent_requests) as executor:
            # Submit all requests
            futures = {
                executor.submit(self._execute_single_request, i): i 
                for i in range(1, self.total_requests + 1)
            }
            
            # Process completed requests
            for future in as_completed(futures):
                request_num = futures[future]
                try:
                    result = future.result()
                    
                    with self.lock:
                        if result['success']:
                            self.completed_count += 1
                            
                            # Record iteration metrics
                            self.iter_metrics.add_iteration(
                                iteration_num=result['request_num'],
                                execution_time=result['execution_time'],
                                peak_ram=result['peak_ram'],
                                peak_cpu=result['peak_cpu'],
                                response_length=result['response_length']
                            )
                            
                            print(f"[{self.completed_count + self.failed_count}/{self.total_requests}] "
                                  f"Request #{result['request_num']} ✓ "
                                  f"{result['execution_time']:.2f}s | "
                                  f"{result['response_length']} chars | "
                                  f"RAM: {result['peak_ram']:.2f}GB | "
                                  f"CPU: {result['peak_cpu']:.1f}%")
                        else:
                            self.failed_count += 1
                            print(f"[{self.completed_count + self.failed_count}/{self.total_requests}] "
                                  f"Request #{result['request_num']} ✗ "
                                  f"Error: {result['error']}")
                            
                            # Still record metrics for failed requests
                            self.iter_metrics.add_iteration(
                                iteration_num=result['request_num'],
                                execution_time=result['execution_time'],
                                peak_ram=result['peak_ram'],
                                peak_cpu=result['peak_cpu'],
                                response_length=0
                            )
                            
                except Exception as e:
                    with self.lock:
                        self.failed_count += 1
                        print(f"[{self.completed_count + self.failed_count}/{self.total_requests}] "
                              f"Request #{request_num} ✗ Exception: {str(e)}")
        
        test_end_time = time.time()
        total_test_time = test_end_time - test_start_time
        
        # Stop monitoring
        all_metrics = self.monitor.stop_monitoring()
        
        print(f"\n{'=' * 70}")
        print("✅ STRESS TEST COMPLETED")
        print(f"{'=' * 70}")
        print(f"\n📊 Summary:")
        print(f"   Total Time: {total_test_time:.2f}s ({total_test_time/60:.2f} minutes)")
        print(f"   Successful: {self.completed_count}/{self.total_requests}")
        print(f"   Failed: {self.failed_count}/{self.total_requests}")
        print(f"   Success Rate: {(self.completed_count/self.total_requests)*100:.1f}%")
        print(f"   Throughput: {self.total_requests/total_test_time:.2f} requests/second")
        
        # Calculate statistics
        stats = self.iter_metrics.get_statistics()
        
        if stats:
            print(f"\n📈 Performance Statistics:")
            print(f"   Avg Execution Time: {stats['avg_execution_time']:.2f}s")
            print(f"   Min Execution Time: {stats['min_execution_time']:.2f}s")
            print(f"   Max Execution Time: {stats['max_execution_time']:.2f}s")
            print(f"   Std Dev: {stats['stddev_execution_time']:.2f}s")
            print(f"   Avg RAM Peak: {stats['avg_ram_peak']:.2f} GB")
            print(f"   Max RAM Peak: {stats['max_ram_peak']:.2f} GB")
            print(f"   Avg CPU: {stats['avg_cpu']:.1f}%")
            print(f"   Max CPU: {stats['max_cpu']:.1f}%")
            
            # System stress analysis
            print(f"\n🔥 System Stress Analysis:")
            ram_total = system_info.get('ram_total_gb', 16)
            ram_usage_percent = (stats['max_ram_peak'] / ram_total) * 100
            
            print(f"   Peak RAM Usage: {ram_usage_percent:.1f}% of total RAM")
            if ram_usage_percent > 90:
                print(f"   ⚠️  CRITICAL: System RAM near capacity!")
            elif ram_usage_percent > 75:
                print(f"   ⚠️  WARNING: High RAM usage detected")
            else:
                print(f"   ✓ RAM usage within acceptable limits")
            
            if stats['max_cpu'] > 90:
                print(f"   ⚠️  CRITICAL: CPU near maximum capacity!")
            elif stats['max_cpu'] > 75:
                print(f"   ⚠️  WARNING: High CPU usage detected")
            else:
                print(f"   ✓ CPU usage within acceptable limits")
        
        # Generate report
        print(f"\n{'=' * 70}")
        config = {
            'model': self.model,
            'iterations': self.total_requests,
            'concurrent': self.concurrent_requests,
            'prompt': self.prompt,
            'successful': self.completed_count,
            'failed': self.failed_count,
            'total_time': total_test_time,
            'throughput': self.total_requests/total_test_time
        }
        
        report_gen = ReportGenerator()
        report_file = report_gen.generate_report(
            system_info=system_info,
            metrics=all_metrics,
            iteration_metrics=self.iter_metrics.iterations,
            statistics=stats,
            config=config
        )
        
        print(f"{'=' * 70}")
        print(f"\n✨ Report saved to: {report_file}")
        print(f"\n🎉 Stress test complete!\n")
        
        return True


def main():
    """Main entry point"""
    
    # High-load configuration
    MODEL = "llama3"  # Using Llama3 for stress test
    TOTAL_REQUESTS = 50  # Total number of requests
    CONCURRENT_REQUESTS = 5  # Number of concurrent requests (3-5)
    PROMPT = "Explain quantum computing in simple terms"
    
    # Allow command line override
    if len(sys.argv) > 1:
        MODEL = sys.argv[1]
    if len(sys.argv) > 2:
        TOTAL_REQUESTS = int(sys.argv[2])
    if len(sys.argv) > 3:
        CONCURRENT_REQUESTS = int(sys.argv[3])
    if len(sys.argv) > 4:
        PROMPT = sys.argv[4]
    
    # Run stress test
    tester = ConcurrentLoadTester(
        model=MODEL, 
        total_requests=TOTAL_REQUESTS,
        concurrent_requests=CONCURRENT_REQUESTS,
        prompt=PROMPT
    )
    success = tester.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
