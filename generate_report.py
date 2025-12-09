"""
PDF Report Generator for Ollama Load Test Results
Creates professional PDF with charts and statistics
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os
from typing import List, Dict, Any
import numpy as np


class ReportGenerator:
    """Generate PDF report with charts and statistics"""
    
    def __init__(self, output_filename: str = None):
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"ollama_load_test_report_{timestamp}.pdf"
        
        self.output_filename = output_filename
        self.chart_dir = "temp_charts"
        os.makedirs(self.chart_dir, exist_ok=True)
        
    def generate_report(self, system_info: Dict, metrics: List[Dict], 
                       iteration_metrics: List[Dict], statistics: Dict,
                       config: Dict):
        """Generate complete PDF report"""
        
        print("\n📊 Generating PDF report...")
        
        # Generate all charts
        chart_files = self._generate_charts(metrics, iteration_metrics)
        
        # Create PDF
        doc = SimpleDocTemplate(self.output_filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title Page
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("Ollama Phi Model", title_style))
        story.append(Paragraph("Load Test Report", title_style))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        # Add stress warnings if applicable
        system_warnings = []
        ram_total = system_info.get('ram_total_gb', 16)
        if statistics.get('max_ram_peak', 0) > 0:
            ram_usage_percent = (statistics['max_ram_peak'] / ram_total) * 100
            if ram_usage_percent > 90:
                system_warnings.append("⚠️ CRITICAL: RAM usage exceeded 90%")
            elif ram_usage_percent > 75:
                system_warnings.append("⚠️ WARNING: High RAM usage detected (>75%)")
        
        if statistics.get('max_cpu', 0) > 90:
            system_warnings.append("⚠️ CRITICAL: CPU usage exceeded 90%")
        elif statistics.get('max_cpu', 0) > 75:
            system_warnings.append("⚠️ WARNING: High CPU usage detected (>75%)")
        
        if system_warnings:
            warning_text = "<br/>".join(system_warnings)
            story.append(Paragraph(f'<font color="red"><b>{warning_text}</b></font>', styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Requests', str(statistics.get('total_iterations', 0))],
            ['Concurrent Requests', str(config.get('concurrent', 1))],
            ['Model Name', config.get('model', 'N/A')],
            ['Success Rate', f"{(config.get('successful', 0) / config.get('iterations', 1) * 100):.1f}%"],
            ['Throughput', f"{config.get('throughput', 0):.2f} req/s"],
            ['Avg Execution Time', f"{statistics.get('avg_execution_time', 0):.2f}s"],
            ['Min Execution Time', f"{statistics.get('min_execution_time', 0):.2f}s"],
            ['Max Execution Time', f"{statistics.get('max_execution_time', 0):.2f}s"],
            ['Avg RAM Usage', f"{statistics.get('avg_ram_peak', 0):.2f} GB"],
            ['Peak RAM Usage', f"{statistics.get('max_ram_peak', 0):.2f} GB ({(statistics.get('max_ram_peak', 0) / ram_total * 100):.1f}%)"],
            ['Avg CPU Usage', f"{statistics.get('avg_cpu', 0):.1f}%"],
            ['Peak CPU Usage', f"{statistics.get('max_cpu', 0):.1f}%"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # System Information
        story.append(Paragraph("System Information", heading_style))
        sys_data = [
            ['Component', 'Specification'],
            ['CPU', system_info.get('cpu_model', 'N/A')],
            ['CPU Cores', f"{system_info.get('cpu_count', 'N/A')} cores / {system_info.get('cpu_threads', 'N/A')} threads"],
            ['CPU Frequency', f"{system_info.get('cpu_freq_mhz', 'N/A')} MHz"],
            ['Total RAM', f"{system_info.get('ram_total_gb', 'N/A')} GB"],
            ['Platform', system_info.get('platform', 'N/A')],
        ]
        
        sys_table = Table(sys_data, colWidths=[2*inch, 4*inch])
        sys_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(sys_table)
        story.append(PageBreak())
        
        # Performance Charts
        story.append(Paragraph("Performance Metrics", heading_style))
        
        for chart_file in chart_files:
            if os.path.exists(chart_file):
                img = Image(chart_file, width=6.5*inch, height=4*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
        
        # Iteration Details
        story.append(Paragraph("Iteration Details", heading_style))
        
        iter_data = [['Iteration', 'Time (s)', 'Peak RAM (GB)', 'Peak CPU (%)', 'Response Length']]
        for it in iteration_metrics:
            iter_data.append([
                str(it['iteration']),
                f"{it['execution_time']:.2f}",
                f"{it['peak_ram_gb']:.2f}",
                f"{it['peak_cpu_percent']:.1f}",
                str(it['response_length'])
            ])
        
        iter_table = Table(iter_data, colWidths=[1*inch, 1.2*inch, 1.5*inch, 1.3*inch, 1.5*inch])
        iter_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(iter_table)
        
        # Build PDF
        doc.build(story)
        
        # Cleanup temp charts
        self._cleanup_charts(chart_files)
        
        print(f"✓ Report generated: {self.output_filename}")
        return self.output_filename
    
    def _generate_charts(self, metrics: List[Dict], iteration_metrics: List[Dict]) -> List[str]:
        """Generate all charts and return file paths"""
        chart_files = []
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Chart 1: RAM Usage Over Time
        chart_file = os.path.join(self.chart_dir, "ram_usage.png")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if metrics:
            timestamps = [(m['timestamp'] - metrics[0]['timestamp']).total_seconds() for m in metrics]
            ram_used = [m['ram_used_gb'] for m in metrics]
            
            ax.plot(timestamps, ram_used, linewidth=2, color='#3498db', label='RAM Used')
            ax.fill_between(timestamps, ram_used, alpha=0.3, color='#3498db')
            ax.set_xlabel('Time (seconds)', fontsize=12)
            ax.set_ylabel('RAM Usage (GB)', fontsize=12)
            ax.set_title('RAM Usage Over Time', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        plt.tight_layout()
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart_file)
        
        # Chart 2: CPU Usage Over Time
        chart_file = os.path.join(self.chart_dir, "cpu_usage.png")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if metrics:
            timestamps = [(m['timestamp'] - metrics[0]['timestamp']).total_seconds() for m in metrics]
            cpu_usage = [m['cpu_percent'] for m in metrics]
            
            ax.plot(timestamps, cpu_usage, linewidth=2, color='#e74c3c', label='CPU Usage')
            ax.fill_between(timestamps, cpu_usage, alpha=0.3, color='#e74c3c')
            ax.set_xlabel('Time (seconds)', fontsize=12)
            ax.set_ylabel('CPU Usage (%)', fontsize=12)
            ax.set_title('CPU Usage Over Time', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            
        plt.tight_layout()
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart_file)
        
        # Chart 3: Execution Time per Iteration
        chart_file = os.path.join(self.chart_dir, "execution_times.png")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if iteration_metrics:
            iterations = [it['iteration'] for it in iteration_metrics]
            exec_times = [it['execution_time'] for it in iteration_metrics]
            
            bars = ax.bar(iterations, exec_times, color='#2ecc71', alpha=0.7, edgecolor='black')
            ax.set_xlabel('Iteration', fontsize=12)
            ax.set_ylabel('Execution Time (seconds)', fontsize=12)
            ax.set_title('Execution Time per Iteration', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}s', ha='center', va='bottom', fontsize=9)
            
        plt.tight_layout()
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart_file)
        
        # Chart 4: Peak RAM per Iteration
        chart_file = os.path.join(self.chart_dir, "peak_ram.png")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if iteration_metrics:
            iterations = [it['iteration'] for it in iteration_metrics]
            peak_rams = [it['peak_ram_gb'] for it in iteration_metrics]
            
            bars = ax.bar(iterations, peak_rams, color='#9b59b6', alpha=0.7, edgecolor='black')
            ax.set_xlabel('Iteration', fontsize=12)
            ax.set_ylabel('Peak RAM (GB)', fontsize=12)
            ax.set_title('Peak RAM Usage per Iteration', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=9)
            
        plt.tight_layout()
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart_file)
        
        return chart_files
    
    def _cleanup_charts(self, chart_files: List[str]):
        """Remove temporary chart files"""
        for chart_file in chart_files:
            try:
                if os.path.exists(chart_file):
                    os.remove(chart_file)
            except:
                pass
        
        try:
            if os.path.exists(self.chart_dir):
                os.rmdir(self.chart_dir)
        except:
            pass
