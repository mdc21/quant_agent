import sys
import logging
from app.agents.pfra import PassiveResearchAgent

logging.basicConfig(level=logging.INFO)

def main():
    agent = PassiveResearchAgent()
    print("Testing dynamic AMFI screen...")
    funds = agent.screen_funds()
    print("\n--- Selected Funds ---")
    for f in funds:
        print(f"{f.ticker} | Score: {f.conviction_score:.2f} | Rationale: {f.rationale}")

if __name__ == "__main__":
    main()
