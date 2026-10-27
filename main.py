import argparse
from src.utils import load_config, setup_logging
from src.orchestrator import ProjectManager

def main():
    parser = argparse.ArgumentParser(description="CSMA Tech Layoffs Reddit Data Pipeline")
    parser.add_argument('--mode', choices=['smoke', 'collect', 'process', 'qa', 'full'], required=True, 
                        help="Execution mode for the pipeline.")
    
    args = parser.parse_args()
    
    setup_logging("main")
    
    try:
        config = load_config()
        manager = ProjectManager(config)
        manager.run(args.mode)
    except Exception as e:
        print(f"Failed to run pipeline: {e}")

if __name__ == "__main__":
    main()
