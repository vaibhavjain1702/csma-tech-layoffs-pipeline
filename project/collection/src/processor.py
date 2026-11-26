import os
import json
import logging
import pandas as pd
from pathlib import Path
from src.utils import get_project_root, setup_logging

logger = setup_logging("processor")

class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.raw_data_dir = get_project_root() / "data" / "raw"
        self.processed_dir = get_project_root() / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.keywords = [k.lower() for k in self.config['keywords']]

    def _matches_keywords(self, text):
        if not text:
            return False
        text_lower = text.lower()
        return any(k in text_lower for k in self.keywords)

    def process(self):
        logger.info("Starting data processing...")
        posts = []
        comments = []
        
        # Traverse raw data directory
        for month_dir in self.raw_data_dir.iterdir():
            if not month_dir.is_dir():
                continue
                
            for file_path in month_dir.iterdir():
                if not file_path.name.endswith(".json"):
                    continue
                    
                with open(file_path, "r") as f:
                    try:
                        batch = json.load(f)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON: {file_path}")
                        continue
                        
                is_posts = file_path.name.startswith("posts")
                
                for item in batch:
                    # Filter by keyword
                    text = item.get("title", "") + " " + item.get("selftext", "") if is_posts else item.get("body", "")
                    
                    if not self._matches_keywords(text):
                        continue
                        
                    # Basic normalization
                    if is_posts:
                        posts.append({
                            "post_id": item.get("id"),
                            "subreddit": item.get("subreddit"),
                            "title": item.get("title"),
                            "body": item.get("selftext"),
                            "created_utc": item.get("created_utc"),
                            "score": item.get("score"),
                            "num_comments": item.get("num_comments"),
                            "author": item.get("author"),
                            "permalink": item.get("permalink")
                        })
                    else:
                        comments.append({
                            "comment_id": item.get("id"),
                            "post_id": item.get("link_id", "").replace("t3_", ""),
                            "parent_id": item.get("parent_id"),
                            "subreddit": item.get("subreddit"),
                            "body": item.get("body"),
                            "created_utc": item.get("created_utc"),
                            "score": item.get("score"),
                            "author": item.get("author")
                        })

        self._save_dataframe(posts, "posts.csv", ["post_id"])
        self._save_dataframe(comments, "comments.csv", ["comment_id"])
        
        logger.info("Data processing complete.")

    def _save_dataframe(self, data, filename, dedupe_subset):
        if not data:
            logger.info(f"No data to save for {filename}")
            return
            
        df = pd.DataFrame(data)
        
        # Deduplicate
        initial_len = len(df)
        df.drop_duplicates(subset=dedupe_subset, inplace=True)
        deduped_len = len(df)
        
        if initial_len > deduped_len:
            logger.info(f"Removed {initial_len - deduped_len} duplicates from {filename}")
            
        out_path = self.processed_dir / filename
        df.to_csv(out_path, index=False, escapechar='\\')
        logger.info(f"Saved {len(df)} rows to {out_path}")
