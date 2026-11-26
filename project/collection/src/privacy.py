import os
import hashlib
import logging
import pandas as pd
from pathlib import Path
from src.utils import get_project_root, setup_logging

logger = setup_logging("privacy")

class PrivacyAgent:
    def __init__(self, config):
        self.config = config
        self.processed_dir = get_project_root() / "data" / "processed"
        
        # Load salt from environment or use a default one for this run if not set
        self.salt = os.environ.get(self.config['privacy']['salt_env_var'], "CSMA_DEFAULT_SALT")
        if self.salt == "CSMA_DEFAULT_SALT":
            logger.warning(f"Using default salt. Set {self.config['privacy']['salt_env_var']} in environment for secure hashing.")

    def _hash_author(self, author_name):
        if pd.isna(author_name) or not author_name:
            return None
        return hashlib.sha256(f"{author_name}{self.salt}".encode('utf-8')).hexdigest()

    def pseudonymize(self):
        logger.info("Starting pseudonymization...")
        
        for filename in ["posts.csv", "comments.csv"]:
            filepath = self.processed_dir / filename
            if not filepath.exists():
                logger.warning(f"{filename} not found, skipping pseudonymization.")
                continue
                
            df = pd.read_csv(filepath)
            
            if "author" in df.columns:
                logger.info(f"Hashing authors in {filename}...")
                df["author_hash"] = df["author"].apply(self._hash_author)
                df.drop(columns=["author"], inplace=True)
                df.to_csv(filepath, index=False)
                logger.info(f"Pseudonymized {filename} successfully.")
            else:
                logger.info(f"No 'author' column found in {filename} (might already be pseudonymized).")

        logger.info("Pseudonymization complete.")
