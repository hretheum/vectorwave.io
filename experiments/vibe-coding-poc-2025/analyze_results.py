#!/usr/bin/env python3
"""
POC Results Analysis Script
Analyzes data and applies decision criteria
"""

import json
import statistics
import pandas as pd
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class POCAnalyzer:
    def __init__(self, data_file: str = 'poc_results.json'):
        """Initialize analyzer with data file"""
        self.data_file = data_file
        self.results = []
        self.decision_threshold = 0.15  # 15% improvement threshold
        
    def load_data(self) -> None:
        """Load results from JSON file"""
        with open(self.data_file, 'r') as f:
            self.results = json.load(f)
        print(f"Loaded {len(self.results)} participant results")
    
    def calculate_paired_deltas(self) -> List[float]:
        """Calculate time differences for each participant"""
        deltas = []
        
        for participant_id in set(r['participant_id'] for r in self.results):
            participant_results = [r for r in self.results if r['participant_id'] == participant_id]
            
            if len(participant_results) != 2:
                print(f"Warning: Participant {participant_id} has {len(participant_results)} results")
                continue
            
            vibe_time = next((r['duration_minutes'] for r in participant_results 
                            if r['tool_type'] == 'Vibe Coding'), None)
            assisted_time = next((r['duration_minutes'] for r in participant_results 
                                if r['tool_type'] == 'Assisted Coding'), None)
            
            if vibe_time and assisted_time:
                # Calculate percentage improvement (negative = vibe is faster)
                delta = (vibe_time - assisted_time) / assisted_time
                deltas.append(delta)
        
        return deltas
    
    def remove_outliers(self, data: List[float], percentile: int = 5) -> List[float]:
        """Remove top and bottom percentile outliers"""
        if len(data) < 10:
            print("Warning: Small sample size, not removing outliers")
            return data
        
        lower = statistics.quantiles(data, n=100)[percentile-1]
        upper = statistics.quantiles(data, n=100)[100-percentile-1]
        
        filtered = [x for x in data if lower <= x <= upper]
        removed = len(data) - len(filtered)
        
        if removed > 0:
            print(f"Removed {removed} outliers ({percentile}% from each tail)")
        
        return filtered
    
    def analyze_time_metrics(self) -> Dict:
        """Analyze time-based metrics"""
        deltas = self.calculate_paired_deltas()
        deltas_clean = self.remove_outliers(deltas)
        
        if not deltas_clean:
            return {"error": "No valid paired data"}
        
        median_improvement = -statistics.median(deltas_clean)  # Negative delta = improvement
        mean_improvement = -statistics.mean(deltas_clean)
        
        # Calculate confidence interval (simplified)
        std_dev = statistics.stdev(deltas_clean) if len(deltas_clean) > 1 else 0
        ci_95 = 1.96 * std_dev / (len(deltas_clean) ** 0.5)
        
        return {
            "median_improvement": median_improvement,
            "mean_improvement": mean_improvement,
            "ci_95_lower": median_improvement - ci_95,
            "ci_95_upper": median_improvement + ci_95,
            "sample_size": len(deltas_clean),
            "meets_threshold": median_improvement >= self.decision_threshold
        }
    
    def analyze_quality_metrics(self) -> Dict:
        """Analyze quality-based metrics"""
        vibe_results = [r for r in self.results if r['tool_type'] == 'Vibe Coding']
        assisted_results = [r for r in self.results if r['tool_type'] == 'Assisted Coding']
        
        metrics = {}
        
        # Test coverage comparison
        vibe_coverage = [r['test_coverage'] for r in vibe_results]
        assisted_coverage = [r['test_coverage'] for r in assisted_results]
        metrics['avg_coverage_vibe'] = statistics.mean(vibe_coverage) if vibe_coverage else 0
        metrics['avg_coverage_assisted'] = statistics.mean(assisted_coverage) if assisted_coverage else 0
        
        # Edge cases found
        vibe_edges = sum(r.get('edge_cases_found', 0) for r in vibe_results)
        assisted_edges = sum(r.get('edge_cases_found', 0) for r in assisted_results)
        metrics['total_edges_vibe'] = vibe_edges
        metrics['total_edges_assisted'] = assisted_edges
        metrics['additional_edges'] = vibe_edges - assisted_edges
        
        # Code review scores
        vibe_scores = [r.get('review_score', 0) for r in vibe_results]
        assisted_scores = [r.get('review_score', 0) for r in assisted_results]
        metrics['avg_review_vibe'] = statistics.mean(vibe_scores) if vibe_scores else 0
        metrics['avg_review_assisted'] = statistics.mean(assisted_scores) if assisted_scores else 0
        
        return metrics
    
    def analyze_experience_metrics(self) -> Dict:
        """Analyze developer experience metrics"""
        vibe_results = [r for r in self.results if r['tool_type'] == 'Vibe Coding']
        assisted_results = [r for r in self.results if r['tool_type'] == 'Assisted Coding']
        
        metrics = {}
        
        # Survey metrics (1-5 scale)
        for metric in ['confidence', 'clarity', 'tool_helpful', 'cognitive_load', 'satisfaction']:
            vibe_values = [r.get(metric, 0) for r in vibe_results]
            assisted_values = [r.get(metric, 0) for r in assisted_results]
            
            metrics[f'{metric}_vibe'] = statistics.mean(vibe_values) if vibe_values else 0
            metrics[f'{metric}_assisted'] = statistics.mean(assisted_values) if assisted_values else 0
        
        return metrics
    
    def apply_decision_criteria(self) -> Tuple[bool, str]:
        """Apply the decision criteria and return recommendation"""
        time_analysis = self.analyze_time_metrics()
        quality_analysis = self.analyze_quality_metrics()
        
        # Criterion 1: ≥15% median time improvement
        criterion1_met = time_analysis.get('meets_threshold', False)
        
        # Criterion 2: At least one additional edge case
        criterion2_met = quality_analysis.get('additional_edges', 0) >= 1
        
        # Both criteria must be met
        adopt = criterion1_met and criterion2_met
        
        reasoning = []
        reasoning.append(f"Time improvement: {time_analysis.get('median_improvement', 0):.1%} "
                        f"({'✅ PASS' if criterion1_met else '❌ FAIL'} - need ≥15%)")
        reasoning.append(f"Additional edge cases: {quality_analysis.get('additional_edges', 0)} "
                        f"({'✅ PASS' if criterion2_met else '❌ FAIL'} - need ≥1)")
        
        return adopt, "\n".join(reasoning)
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 60)
        report.append("POC VIBE CODING ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Time Analysis
        time_analysis = self.analyze_time_metrics()
        report.append("TIME METRICS")
        report.append("-" * 40)
        report.append(f"Median improvement: {time_analysis.get('median_improvement', 0):.1%}")
        report.append(f"Mean improvement: {time_analysis.get('mean_improvement', 0):.1%}")
        report.append(f"95% CI: [{time_analysis.get('ci_95_lower', 0):.1%}, "
                     f"{time_analysis.get('ci_95_upper', 0):.1%}]")
        report.append(f"Sample size: {time_analysis.get('sample_size', 0)}")
        report.append("")
        
        # Quality Analysis
        quality_analysis = self.analyze_quality_metrics()
        report.append("QUALITY METRICS")
        report.append("-" * 40)
        report.append(f"Test Coverage - Vibe: {quality_analysis.get('avg_coverage_vibe', 0):.1f}% "
                     f"vs Assisted: {quality_analysis.get('avg_coverage_assisted', 0):.1f}%")
        report.append(f"Edge Cases - Vibe: {quality_analysis.get('total_edges_vibe', 0)} "
                     f"vs Assisted: {quality_analysis.get('total_edges_assisted', 0)}")
        report.append(f"Review Score - Vibe: {quality_analysis.get('avg_review_vibe', 0):.1f}/120 "
                     f"vs Assisted: {quality_analysis.get('avg_review_assisted', 0):.1f}/120")
        report.append("")
        
        # Experience Analysis
        experience_analysis = self.analyze_experience_metrics()
        report.append("EXPERIENCE METRICS (1-5 scale)")
        report.append("-" * 40)
        for metric in ['confidence', 'clarity', 'tool_helpful', 'satisfaction']:
            vibe_score = experience_analysis.get(f'{metric}_vibe', 0)
            assisted_score = experience_analysis.get(f'{metric}_assisted', 0)
            report.append(f"{metric.title():12} - Vibe: {vibe_score:.1f} vs Assisted: {assisted_score:.1f}")
        report.append("")
        
        # Decision
        adopt, reasoning = self.apply_decision_criteria()
        report.append("DECISION CRITERIA")
        report.append("-" * 40)
        report.append(reasoning)
        report.append("")
        report.append(f"RECOMMENDATION: {'✅ ADOPT VIBE CODING' if adopt else '❌ CONTINUE WITH ASSISTED CODING'}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def generate_visualizations(self) -> None:
        """Generate visualization plots"""
        # Set style
        sns.set_style("whitegrid")
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Time comparison
        vibe_times = [r['duration_minutes'] for r in self.results if r['tool_type'] == 'Vibe Coding']
        assisted_times = [r['duration_minutes'] for r in self.results if r['tool_type'] == 'Assisted Coding']
        
        axes[0, 0].boxplot([assisted_times, vibe_times], labels=['Assisted', 'Vibe'])
        axes[0, 0].set_title('Task Duration Comparison')
        axes[0, 0].set_ylabel('Minutes')
        
        # Quality metrics
        quality = self.analyze_quality_metrics()
        metrics = ['Test Coverage', 'Edge Cases', 'Review Score']
        vibe_values = [
            quality.get('avg_coverage_vibe', 0),
            quality.get('total_edges_vibe', 0) * 10,  # Scale for visibility
            quality.get('avg_review_vibe', 0) / 1.2   # Scale to 100
        ]
        assisted_values = [
            quality.get('avg_coverage_assisted', 0),
            quality.get('total_edges_assisted', 0) * 10,
            quality.get('avg_review_assisted', 0) / 1.2
        ]
        
        x = range(len(metrics))
        width = 0.35
        axes[0, 1].bar([i - width/2 for i in x], assisted_values, width, label='Assisted')
        axes[0, 1].bar([i + width/2 for i in x], vibe_values, width, label='Vibe')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(metrics)
        axes[0, 1].set_title('Quality Metrics Comparison')
        axes[0, 1].legend()
        
        # Experience ratings
        experience = self.analyze_experience_metrics()
        metrics = ['Confidence', 'Clarity', 'Helpful', 'Satisfaction']
        vibe_exp = [experience.get(f'{m.lower()}_vibe', 0) for m in metrics]
        assisted_exp = [experience.get(f'{m.lower()}_assisted', 0) for m in metrics]
        
        axes[1, 0].plot(metrics, assisted_exp, 'o-', label='Assisted')
        axes[1, 0].plot(metrics, vibe_exp, 's-', label='Vibe')
        axes[1, 0].set_title('Developer Experience (1-5 scale)')
        axes[1, 0].set_ylim([1, 5])
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Paired improvement
        deltas = self.calculate_paired_deltas()
        axes[1, 1].hist([-d * 100 for d in deltas], bins=10, edgecolor='black')
        axes[1, 1].axvline(x=15, color='red', linestyle='--', label='15% threshold')
        axes[1, 1].set_title('Time Improvement Distribution')
        axes[1, 1].set_xlabel('% Improvement (Vibe vs Assisted)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('poc_analysis_visualizations.png', dpi=150)
        print("Saved visualizations to poc_analysis_visualizations.png")
        plt.show()

def main():
    """Main analysis workflow"""
    print("POC Results Analysis Tool")
    print("=" * 40)
    
    analyzer = POCAnalyzer()
    
    # Load data
    try:
        analyzer.load_data()
    except FileNotFoundError:
        print("\nError: poc_results.json not found")
        print("Please ensure results are exported to poc_results.json")
        return
    
    # Generate report
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Save report
    with open('poc_analysis_report.txt', 'w') as f:
        f.write(report)
    print("\nReport saved to poc_analysis_report.txt")
    
    # Generate visualizations
    try:
        analyzer.generate_visualizations()
    except ImportError:
        print("\nNote: Install matplotlib and seaborn for visualizations")
        print("pip install matplotlib seaborn")

if __name__ == "__main__":
    main()