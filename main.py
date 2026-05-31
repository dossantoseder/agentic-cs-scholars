#!/usr/bin/env python
"""
Main entry point for the agentic system.
Orchestrates data collection and enrichment pipeline.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.OrchestratorAgent import OrchestratorAgent
from src.agents.LoggingAgent import LoggingAgent


def print_section(title: str) -> None:
    """Prints a formatted section title."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def save_execution_report(results: dict, output_dir: Path) -> None:
    """Saves execution report to JSON file."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": results.get("status"),
        "results": results.get("results", {}),
        "error": results.get("error")
    }
    
    report_path = output_dir / "execution_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nExecution report saved to: {report_path}")


def main() -> None:
    print_section("Agentic CS Scholars System")
    print("System for collecting and enriching CNPq researcher data")
    
    planner = OrchestratorAgent()
    logger = LoggingAgent()
    
    logger.log_agent_start("Main", "execution_001")
    
    url = input("\nEnter CNPq page URL: ").strip()
    
    if not url:
        print("Error: URL is required")
        logger.log_error("Main", "No URL provided", "execution_001")
        return
    
    print("\nOptions:")
    print("1. Full pipeline (collect + enrich)")
    print("2. Only collect data (no enrichment)")
    print("3. Only enrichment (requires existing data)")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    output_dir = Path("./data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if choice == "1":
        print_section("Starting Full Pipeline")
        result = planner.execute({
            "goal": "collect_data",
            "parameters": {
                "url": url,
                "output_dir": "./data"
            }
        })
    elif choice == "2":
        print_section("Starting Data Collection Only")
        from src.agents.web_scraper_agent import WebScraperAgent
        scraper = WebScraperAgent()
        result = scraper.execute({"url": url, "max_retries": 3})
        
        if result.get("status") == "success":
            raw_path = output_dir / "raw_data.json"
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(result.get("data", []), f, ensure_ascii=False, indent=2)
            print(f"\nRaw data saved to: {raw_path}")
            print(f"Records collected: {result.get('record_count', 0)}")
    elif choice == "3":
        print_section("Starting Enrichment Only")
        data_path = output_dir / "pesquisadores.json"
        
        if not data_path.exists():
            print(f"Error: No data found at {data_path}")
            print("Please run collection first (option 1 or 2)")
            logger.log_error("Main", "No data found for enrichment", "execution_001")
            return
        
        from src.agents.enrichment_agent import EnrichmentAgent
        with open(data_path, 'r', encoding='utf-8') as f:
            researchers = json.load(f)
        
        enrichment = EnrichmentAgent()
        result = enrichment.execute({
            "researchers": researchers,
            "output_dir": "./data"
        })
    else:
        print("Invalid option. Exiting.")
        logger.log_error("Main", f"Invalid option: {choice}", "execution_001")
        return
    
    if result.get("status") == "success":
        print_section("Execution Completed Successfully")
        print(f"Status: {result.get('status')}")
        
        if 'record_count' in result:
            print(f"Records processed: {result['record_count']}")
        if 'enriched_count' in result:
            print(f"Enriched records: {result['enriched_count']}")
        if 'failed_count' in result:
            print(f"Failed records: {result['failed_count']}")
        
        save_execution_report(result, output_dir)
        logger.log_agent_end("Main", 0, "execution_001")
        
        print("\nTo visualize the data, run:")
        print("  streamlit run run_dashboard.py")
    else:
        print_section("Execution Failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        logger.log_error("Main", result.get('error', 'Unknown error'), "execution_001")


if __name__ == "__main__":
    main()