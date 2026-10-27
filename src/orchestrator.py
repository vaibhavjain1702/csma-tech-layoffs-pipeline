import logging
from src.collector import ArcticShiftCollector
from src.processor import DataProcessor
from src.privacy import PrivacyAgent
from src.qa import QAAgent
from src.utils import setup_logging

logger = setup_logging("orchestrator")

class ProjectManager:
    def __init__(self, config):
        self.config = config
        
    def run(self, mode):
        logger.info(f"Starting pipeline in mode: {mode}")
        
        if mode in ["smoke", "collect", "full"]:
            logger.info("--- Phase: Data Collection ---")
            collector = ArcticShiftCollector(self.config)
            
            # If smoke test, override limit and date range temporarily
            if mode == "smoke":
                logger.info("SMOKE TEST: Limiting collection.")
                collector.config['subreddits'] = [collector.config['subreddits'][0]] # just first subreddit
                collector.limit = 10
                collector.collect(max_batches=1)
            else:
                collector.collect()
            
        if mode in ["smoke", "process", "full"]:
            logger.info("--- Phase: Data Processing ---")
            processor = DataProcessor(self.config)
            processor.process()
            
            logger.info("--- Phase: Privacy ---")
            privacy = PrivacyAgent(self.config)
            privacy.pseudonymize()
            
        if mode in ["smoke", "qa", "full"]:
            logger.info("--- Phase: QA ---")
            qa = QAAgent(self.config)
            qa.run_qa()
            
        logger.info("Pipeline execution finished.")
