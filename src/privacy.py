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
        
        # The salt must come from the environment; there is no built-in fallback,
        # since a publicly known salt would make the pseudonyms reversible.
        env_var = self.config['privacy']['salt_env_var']
        self.salt = os.environ.get(env_var)
        if not self.salt:
            raise RuntimeError(f"Set the {env_var} environment variable to a secret string before running pseudonymization.")

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
