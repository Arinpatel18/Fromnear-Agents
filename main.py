#!/usr/bin/env python3
"""
Main entry point for the AI-driven Sales & Marketing Pipeline.

Usage:
    python main.py <website_url> <instagram_url>

Example:
    python main.py "https://www.example.com" "_example_store"
"""

import sys
import asyncio
import json
import logging
from src.graph import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    if len(sys.argv) < 3:
        print("Usage: python main.py <website_url> <instagram_url>")
        print()
        print("Example:")
        print('  python main.py "https://www.shopclues.com" "_fashion_store_44"')
        print()
        sys.exit(1)
    
    website_url = sys.argv[1]
    instagram_url = sys.argv[2]
    
    try:
        # Run the pipeline
        result = asyncio.run(run_pipeline(website_url, instagram_url))
        
        # Extract aggregated output
        aggregated = result.get("aggregated_output", {})
        
        # Print markdown report
        if aggregated.get("markdown_report"):
            print("\n" + "=" * 80)
            print(aggregated["markdown_report"])
            print("=" * 80)
        
        # Save report to file
        output_filename = "report.md"
        if aggregated.get("markdown_report"):
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(aggregated["markdown_report"])
            logger.info(f"✓ Report saved to {output_filename}")
        
        # Save JSON data
        json_filename = "report.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump({
                "sales": aggregated.get("sales_data", {}),
                "marketing": aggregated.get("marketing_data", {})
            }, f, indent=2)
        logger.info(f"✓ JSON data saved to {json_filename}")
        
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
