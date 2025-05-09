#!/usr/bin/env python3
"""
Batch Carbon Footprint Analysis

This script runs the full agentic carbon footprint analysis flow on multiple product URLs,
with multiple runs per product to generate a robust dataset of carbon footprint analyses.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env.local')

# Update with your name to group your own traces
os.environ['LANGCHAIN_PROJECT'] = 'batch-product-analysis'

# Import the graph setup function from api.graph
from api.graph import setup_graph
from state import FootprintState

# Define a list of product URLs to analyze
product_urls = [
    "https://www.apple.com/iphone-15-pro/",          # Electronics - iPhone
    "https://www.patagonia.com/product/mens-better-sweater-fleece-jacket/25528.html", # Clothing - Patagonia jacket
    "https://www.ikea.com/us/en/p/ivar-chair-pine-90263902/", # Furniture - IKEA chair
    "https://www.nike.com/t/air-jordan-1-retro-high-og-mens-shoes-VdpsB7/DZ5485-042", # Footwear - Nike shoes
    "https://www.target.com/p/7-5-34-artificial-fiddle-leaf-fig-plant-in-pot-threshold-8482-designed-with-studio-mcgee/-/A-84146617", # Home decor - Artificial plant
    "https://www.samsung.com/us/tvs/uhd-tvs/55-class-cu7000-crystal-uhd-4k-smart-tv-un55cu7000fxza/", # Electronics - TV
    "https://www.amazon.com/AmazonBasics-Sheet-Set-Twin-Navy/dp/B06XS7KV1K/", # Home textiles - Sheet set
    "https://www.rei.com/product/168489/nalgene-wide-mouth-water-bottle-32-fl-oz", # Outdoor gear - Water bottle
    "https://www.whirlpool.com/kitchen/refrigeration/refrigerators/french-door/p.36-inch-wide-french-door-refrigerator-25-cu.-ft.wrf555sdfz.html", # Appliances - Refrigerator
    "https://www.bestbuy.com/site/logitech-mx-master-3s-wireless-performance-mouse-with-ultrafast-scrolling-ergonomic-design-8k-dpi-optical-tracking-bluetooth-quiet-clicks-usb-c-graphite/6504032.p" # Computer peripherals - Mouse
]


async def run_single_analysis(product_url: str, run_id: int) -> Dict[str, Any]:
    """
    Run a single analysis for a product URL with a unique run ID.
    
    Args:
        product_url: The URL of the product to analyze
        run_id: Unique identifier for this run
        
    Returns:
        Dictionary with analysis results
    """
    try:
        print(f"Starting analysis for {product_url} (run {run_id})")
        # Set up graph for this run
        graph = setup_graph()
        
        # Create unique thread ID for this run
        config = {"configurable": {"thread_id": f"batch-run-{run_id}-{int(time.time())}"}} 
        
        # Prepare initial state with the product URL
        initial_state: FootprintState = {
            "url": product_url,
            "user_input": f"Analyze product from URL: {product_url}",
            "messages": [("human", f"Analyze carbon footprint for product at URL: {product_url}")]
        }
        
        # Run the graph
        result = await graph.ainvoke(
            initial_state,
            config
        )
        
        # Extract key information from result
        carbon_footprints = {}
        total_carbon = 0
        
        for phase in ["materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
            if phase in result and "carbon" in result[phase]:
                carbon_value = result[phase]["carbon"]
                carbon_footprints[phase] = carbon_value
                if isinstance(carbon_value, (int, float)):
                    total_carbon += carbon_value
        
        # Create structured output
        output = {
            "product_url": product_url,
            "run_id": run_id,
            "brand": result.get("brand", "Unknown"),
            "category": result.get("category", "Unknown"),
            "description": result.get("short_description", "Unknown"),
            "carbon_total": total_carbon,
            "carbon_by_phase": carbon_footprints,
            "timestamp": time.time(),
            "success": True
        }
        
        print(f"Completed analysis for {product_url} (run {run_id}): {total_carbon} kg CO2e")
        return output
    
    except Exception as e:
        print(f"Error in analysis for {product_url} (run {run_id}): {str(e)}")
        # Return error information if analysis fails
        return {
            "product_url": product_url,
            "run_id": run_id,
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


async def batch_process(urls: List[str], runs_per_url: int = 10, max_concurrent: int = 2) -> List[Dict[str, Any]]:
    """
    Process multiple product URLs with multiple runs each.
    
    Args:
        urls: List of product URLs to analyze
        runs_per_url: Number of runs to perform for each URL
        max_concurrent: Maximum number of concurrent runs
        
    Returns:
        List of dictionaries with results from all runs
    """
    all_tasks = []
    all_results = []
    run_counter = 0
    
    # Generate all tasks
    for url in urls:
        for i in range(runs_per_url):
            all_tasks.append((url, run_counter))
            run_counter += 1
    
    # Process tasks in batches to avoid overwhelming resources
    total_tasks = len(all_tasks)
    print(f"Processing {total_tasks} tasks...")
    
    for i in range(0, total_tasks, max_concurrent):
        batch = all_tasks[i:i+max_concurrent]
        tasks = [run_single_analysis(url, run_id) for url, run_id in batch]
        batch_results = await asyncio.gather(*tasks)
        all_results.extend(batch_results)
        print(f"Completed {min(i+max_concurrent, total_tasks)}/{total_tasks} tasks")

        # Save incremental results to avoid losing data on error
        save_results(all_results, "results/interim_results.json")
    
    return all_results


def save_results(results: List[Dict[str, Any]], filename: str):
    """
    Save results to a JSON file.
    
    Args:
        results: List of result dictionaries
        filename: Name of file to save to
    """
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {filename}")


def analyze_results(results: List[Dict[str, Any]]):
    """
    Analyze the results and provide statistics.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        DataFrame with analysis results
    """
    # Filter successful runs
    successful_runs = [r for r in results if r.get("success", False)]
    
    if not successful_runs:
        print("No successful runs to analyze")
        return None, None
    
    # Create dataframe
    df = pd.DataFrame(successful_runs)
    
    # Add columns for each phase's carbon footprint
    for phase in ["materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
        df[f"{phase}_carbon"] = df["carbon_by_phase"].apply(
            lambda x: x.get(phase, None) if isinstance(x, dict) else None
        )
    
    # Group by product URL and calculate statistics
    summary = df.groupby("product_url").agg({
        "brand": "first",
        "category": "first",
        "description": "first",
        "carbon_total": ["mean", "std", "min", "max", "count"],
        "materials_carbon": ["mean", "std"],
        "manufacturing_carbon": ["mean", "std"],
        "packaging_carbon": ["mean", "std"],
        "transportation_carbon": ["mean", "std"],
        "use_carbon": ["mean", "std"],
        "eol_carbon": ["mean", "std"]
    })
    
    return df, summary


def visualize_results(df, summary, timestamp):
    """
    Create visualizations of the results.
    
    Args:
        df: DataFrame with all results
        summary: Summary DataFrame with statistics
        timestamp: Timestamp for saving files
    """
    if df is None or df.empty:
        print("No data to visualize")
        return
    
    # Create directory for results if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Create simple visualizations
    plt.figure(figsize=(14, 8))
    
    # Create a bar chart of average carbon footprints by product
    plt.subplot(2, 1, 1)
    avg_carbon = df.groupby('product_url')['carbon_total'].mean().sort_values(ascending=False)
    product_labels = [df[df['product_url'] == url]['description'].iloc[0] for url in avg_carbon.index]
    
    # Truncate long product descriptions
    product_labels = [label[:30] + '...' if len(label) > 30 else label for label in product_labels]
    
    plt.bar(range(len(product_labels)), avg_carbon.values)
    plt.xticks(range(len(product_labels)), product_labels, rotation=45, ha='right')
    plt.title('Average Total Carbon Footprints by Product')
    plt.xlabel('Product')
    plt.ylabel('Carbon Footprint (kg CO2e)')
    
    # Create a stacked bar chart of average carbon footprints by phase for each product
    plt.subplot(2, 1, 2)
    phases = ['materials_carbon', 'manufacturing_carbon', 'packaging_carbon', 
              'transportation_carbon', 'use_carbon', 'eol_carbon']
    phase_avgs = df.groupby('product_url')[phases].mean()
    
    bottom = None
    for phase in phases:
        plt.bar(range(len(phase_avgs.index)), phase_avgs[phase], bottom=bottom, 
                label=phase.replace('_carbon', ''))
        if bottom is None:
            bottom = phase_avgs[phase].values
        else:
            bottom = bottom + phase_avgs[phase].values
    
    plt.title('Average Carbon Footprint by Phase for Each Product')
    plt.xlabel('Product')
    plt.ylabel('Carbon Footprint (kg CO2e)')
    plt.legend(title='Phase')
    plt.xticks(range(len(phase_avgs.index)), product_labels, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(f'results/carbon_footprint_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')
    
    # Create a consistency analysis chart
    # Calculate coefficient of variation (CV) for each product and phase
    # CV = std / mean * 100%
    cv_data = {}
    for url in df['product_url'].unique():
        product_df = df[df['product_url'] == url]
        cv_data[url] = {}
        
        # Calculate CV for total carbon
        mean = product_df['carbon_total'].mean()
        std = product_df['carbon_total'].std()
        cv = (std / mean * 100) if mean > 0 else float('nan')
        cv_data[url]['total'] = cv
        
        # Calculate CV for each phase
        for phase in phases:
            mean = product_df[phase].mean()
            std = product_df[phase].std()
            cv = (std / mean * 100) if mean > 0 else float('nan')
            cv_data[url][phase] = cv
    
    # Create a DataFrame for visualization
    cv_df = pd.DataFrame(cv_data).T
    cv_df.index = [df[df['product_url'] == url]['description'].iloc[0] for url in cv_df.index]
    
    # Save CV data to CSV
    cv_df.to_csv(f'results/consistency_analysis_{timestamp}.csv')
    
    # Create a simple heatmap-like visualization
    plt.figure(figsize=(14, 8))
    plt.imshow(cv_df.values, cmap='YlGnBu')
    plt.colorbar(label='Coefficient of Variation (%)')
    plt.title('Coefficient of Variation (%) Across Multiple Runs')
    plt.ylabel('Product')
    plt.xlabel('Carbon Footprint Component')
    plt.xticks(range(len(cv_df.columns)), cv_df.columns, rotation=45, ha='right')
    plt.yticks(range(len(cv_df.index)), product_labels)
    plt.tight_layout()
    plt.savefig(f'results/consistency_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')
    
    print(f"Visualizations saved to results/ directory with timestamp {timestamp}")


async def main():
    """
    Main entry point for the script.
    """
    # Set parameters
    test_mode = True  # Set to False for full analysis
    runs_per_url = 2 if test_mode else 10
    max_concurrent = 2
    
    timestamp = int(time.time())
    
    print(f"Starting batch analysis with {'TEST MODE' if test_mode else 'FULL MODE'}")
    print(f"Processing {len(product_urls)} products with {runs_per_url} runs each ({len(product_urls) * runs_per_url} total runs)")
    print(f"Using max concurrency of {max_concurrent}")
    
    # Run the batch process
    results = await batch_process(product_urls, runs_per_url=runs_per_url, max_concurrent=max_concurrent)
    
    # Save final results
    save_results(results, f"results/batch_results_{timestamp}.json")
    
    # Analyze results
    df, summary = analyze_results(results)
    
    # Print summary to console
    if summary is not None:
        print("\nSummary of results:")
        print(summary)
        
        # Save summary to CSV
        summary.to_csv(f"results/summary_{timestamp}.csv")
    
    # Create visualizations
    visualize_results(df, summary, timestamp)
    
    print("\nBatch analysis complete!")


if __name__ == "__main__":
    # Create results directory
    os.makedirs("results", exist_ok=True)

    # Ensure the script has the proper permissions
    try:
        import stat
        current_permissions = os.stat(__file__).st_mode
        os.chmod(__file__, current_permissions | stat.S_IEXEC)
        print(f"Made script executable: {__file__}")
    except Exception as e:
        print(f"Could not make script executable: {e}")

    # Run the main function
    asyncio.run(main())