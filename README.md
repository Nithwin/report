# Ollama Phi Model Load Test

A comprehensive load testing tool for the Ollama Phi model that monitors system performance (CPU, RAM) and generates professional PDF reports with charts and statistics.

## Features

- 🚀 **Load Testing**: Run multiple iterations to stress test the Ollama Phi model
- 📊 **Real-time Monitoring**: Track CPU and RAM usage during model execution
- 📈 **Performance Metrics**: Measure execution time, peak RAM, and CPU usage per iteration
- 📄 **PDF Reports**: Generate professional reports with charts and detailed statistics
- 🎯 **Configurable**: Customize model name, iterations, and test prompts

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running (http://localhost:11434)
- Ollama Phi model downloaded (`ollama pull phi`)

## Installation

1. Install required dependencies:
```powershell
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the load test with default settings (10 iterations):
```powershell
python run_analysis.py
```

### Custom Configuration

You can customize the test by editing `run_analysis.py` or passing command-line arguments:

```powershell
# Custom model name
python run_analysis.py phi3

# Custom model and iterations
python run_analysis.py phi3 20

# Custom model, iterations, and prompt
python run_analysis.py phi3 20 "Write a short poem about AI"
```

### Configuration Options

Edit these variables in `run_analysis.py`:
- `MODEL`: Model name (default: "phi")
- `ITERATIONS`: Number of test iterations (default: 10)
- `PROMPT`: Test prompt (default: "Explain what artificial intelligence is in 2 sentences")

## Output

The tool generates:
- **Console Output**: Real-time progress and statistics
- **PDF Report**: Comprehensive report with:
  - Executive summary
  - System specifications
  - Performance charts (RAM usage, CPU usage, execution times)
  - Detailed iteration statistics
  - Professional formatting

Report filename format: `ollama_load_test_report_YYYYMMDD_HHMMSS.pdf`

## Project Structure

```
report/
├── run_analysis.py       # Main orchestration script
├── system_monitor.py     # System resource monitoring
├── ollama_client.py      # Ollama API client
├── generate_report.py    # PDF report generator
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Metrics Tracked

- **Execution Time**: Time taken for each model inference
- **RAM Usage**: Total and peak RAM usage during execution
- **CPU Usage**: Overall and per-core CPU utilization
- **Response Length**: Character count of model responses
- **Statistics**: Average, min, max, and standard deviation

## Troubleshooting

**Ollama not connecting:**
- Ensure Ollama is running: `ollama serve`
- Check if accessible: `curl http://localhost:11434/api/tags`

**Model not found:**
- Pull the model: `ollama pull phi`
- List available models: `ollama list`

**Dependencies issues:**
- Reinstall: `pip install -r requirements.txt --upgrade`

## Example Output

```
🚀 OLLAMA PHI MODEL LOAD TEST
======================================================================

📋 Configuration:
   Model: phi
   Iterations: 10
   Prompt: Explain what artificial intelligence is in 2 sentences...

✓ Ollama is running
✓ Model 'phi' is available

💻 System Information:
   CPU: Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz
   Cores: 8 (8 threads)
   RAM: 16.0 GB

🏁 STARTING LOAD TEST
======================================================================

[1/10] Running iteration 1...
   ✓ Completed in 2.45s | Response: 234 chars | RAM: 8.23GB | CPU: 45.2%
...
```

## License

MIT License - Feel free to use and modify as needed.
