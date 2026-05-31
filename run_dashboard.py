#!/usr/bin/env python
"""
Script to run the Streamlit dashboard for visualizing researcher data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.dashboard_agent import DashboardAgent


def main() -> None:
    """
    Main entry point for dashboard.
    Executes the DashboardAgent in run mode.
    """
    print("=" * 60)
    print(" Starting CNPq Researchers Dashboard")
    print("=" * 60)
    print("\nDashboard will open in your browser shortly...")
    print("Press Ctrl+C to stop the server\n")
    
    agent = DashboardAgent()
    agent.execute({"mode": "run"})


if __name__ == "__main__":
    main()