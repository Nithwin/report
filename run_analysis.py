"""
Main Orchestration Script for Ollama Phi Load Testing
Runs load test and generates comprehensive PDF report
"""

import sys
import time
from datetime import datetime
from system_monitor import SystemMonitor, IterationMetrics
from ollama_client import OllamaClient
from generate_report import ReportGenerator


class LoadTester:
    """Orchestrate load testing of Ollama Phi model"""
    
    def __init__(self, model: str = "phi", iterations: int = 10, 
                 prompt: str = "Explain what artificial intelligence is in 2 sentences"):
        self.model = model
        self.iterations = iterations
        self.prompt = prompt
        self.ollama = OllamaClient()
        self.monitor = SystemMonitor()
        self.iter_metrics = IterationMetrics()
        
    def run(self):
        """Execute the load test"""
        print("=" * 70)
        print("🚀 OLLAMA PHI MODEL LOAD TEST")
        print("=" * 70)
        print(f"\n📋 Configuration:")
        print(f"   Model: {self.model}")
        print(f"   Iterations: {self.iterations}")
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
        
        if not available_models:
            print("⚠ Warning: Could not list models, attempting to proceed anyway...")
        elif self.model not in available_models:
            print(f"\n⚠ Warning: Model '{self.model}' not found in available models:")
            for m in available_models:
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
        print("🏁 STARTING LOAD TEST")
        print(f"{'=' * 70}\n")
        
        self.monitor.start_monitoring()
        test_start_time = time.time()
        
        successful_iterations = 0
        failed_iterations = 0
        
        # Run iterations
        for i in range(1, self.iterations + 1):
            print(f"[{i}/{self.iterations}] Running iteration {i}...")
            
            iteration_start_time = time.time()
            
            # Get baseline metrics
            import psutil
            baseline_ram = psutil.virtual_memory().used / (1024**3)
            
            # Execute model
            result = self.ollama.generate(self.model, self.prompt)
            
            iteration_end_time = time.time()
            execution_time = iteration_end_time - iteration_start_time
            
            if result['success']:
                successful_iterations += 1
                response_length = len(result['response'])
                
                # Get peak metrics during this iteration
                peak_ram = psutil.virtual_memory().used / (1024**3)
                avg_cpu = psutil.cpu_percent(interval=0.1)
                
                # Record iteration metrics
                self.iter_metrics.add_iteration(
                    iteration_num=i,
                    execution_time=execution_time,
                    peak_ram=peak_ram,
                    avg_cpu=avg_cpu,
                    response_length=response_length
                )
                
                print(f"   ✓ Completed in {execution_time:.2f}s | Response: {response_length} chars | RAM: {peak_ram:.2f}GB | CPU: {avg_cpu:.1f}%")
            else:
                failed_iterations += 1
                print(f"   ✗ Failed: {result['error']}")
                
                # Still record metrics for failed iterations
                peak_ram = psutil.virtual_memory().used / (1024**3)
                avg_cpu = psutil.cpu_percent(interval=0.1)
                
                self.iter_metrics.add_iteration(
                    iteration_num=i,
                    execution_time=execution_time,
                    peak_ram=peak_ram,
                    avg_cpu=avg_cpu,
                    response_length=0
                )
            
            # Small delay between iterations
            if i < self.iterations:
                time.sleep(0.5)
        
        test_end_time = time.time()
        total_test_time = test_end_time - test_start_time
        
        # Stop monitoring
        all_metrics = self.monitor.stop_monitoring()
        
        print(f"\n{'=' * 70}")
        print("✅ LOAD TEST COMPLETED")
        print(f"{'=' * 70}")
        print(f"\n📊 Summary:")
        print(f"   Total Time: {total_test_time:.2f}s")
        print(f"   Successful: {successful_iterations}/{self.iterations}")
        print(f"   Failed: {failed_iterations}/{self.iterations}")
        
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
        
        # Generate report
        print(f"\n{'=' * 70}")
        config = {
            'model': self.model,
            'iterations': self.iterations,
            'prompt': self.prompt,
            'successful': successful_iterations,
            'failed': failed_iterations,
            'total_time': total_test_time
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
        print(f"\n🎉 Load test complete!\n")
        
        return True


def main():
    """Main entry point"""
    
    # Configuration (can be modified or made into CLI args)
    MODEL = "phi"  # Change this to your model name (e.g., "phi3", "phi:latest")
    ITERATIONS = 10  # Number of test iterations
    PROMPT = "Explain what artificial intelligence is in 2 sentences"
    
    # Allow command line override
    if len(sys.argv) > 1:
        MODEL = sys.argv[1]
    if len(sys.argv) > 2:
        ITERATIONS = int(sys.argv[2])
    if len(sys.argv) > 3:
        PROMPT = sys.argv[3]
    
    # Run load test
    tester = LoadTester(model=MODEL, iterations=ITERATIONS, prompt=PROMPT)
    success = tester.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
