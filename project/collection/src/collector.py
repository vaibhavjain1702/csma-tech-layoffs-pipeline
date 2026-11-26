import os
import time
import json
import logging
from datetime import datetime, timezone
import requests
import urllib3
from src.utils import get_project_root, setup_logging

# Suppress insecure request warnings since we are disabling SSL verification for the community API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logging("collector")

class ArcticShiftCollector:
    def __init__(self, config):
        self.config = config
        self.base_url = "https://arctic-shift.photon-reddit.com/api"
        self.raw_data_dir = get_project_root() / "data" / "raw"
        self.checkpoint_dir = get_project_root() / "checkpoints"
        
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.limit = self.config['collection']['limit_per_request']
        self.max_retries = self.config['collection']['max_retries']
        self.delay = self.config['collection']['rate_limit_delay_seconds']

    def _get_checkpoint(self, subreddit, item_type):
        """Loads the last timestamp fetched for a given subreddit and item_type."""
        cp_file = self.checkpoint_dir / f"{item_type}_{subreddit}_checkpoint.json"
        if cp_file.exists():
            with open(cp_file, "r") as f:
                return json.load(f).get("last_timestamp")
        
        # Parse start date if no checkpoint
        dt = datetime.strptime(self.config['date_range']['start'], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())

    def _save_checkpoint(self, subreddit, item_type, timestamp):
        """Saves the last timestamp fetched."""
        cp_file = self.checkpoint_dir / f"{item_type}_{subreddit}_checkpoint.json"
        with open(cp_file, "w") as f:
            json.dump({"last_timestamp": timestamp}, f)

    def _make_request(self, endpoint, params):
        """Makes an HTTP GET request with retries."""
        url = f"{self.base_url}/{endpoint}"
        retries = 0
        while retries <= self.max_retries:
            try:
                time.sleep(self.delay)
                response = requests.get(url, params=params, timeout=30, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data and data["error"]:
                        logger.error(f"API Error: {data['error']}")
                        # If timeout from API, sleep longer
                        if "Timeout" in data["error"]:
                            time.sleep(self.delay * 5)
                            retries += 1
                            continue
                        return None
                    return data.get("data", [])
                elif response.status_code == 429:
                    logger.warning("Rate limited, backing off...")
                    time.sleep(self.delay * (2 ** retries))
                else:
                    logger.warning(f"Status {response.status_code} from {url}")
            except Exception as e:
                logger.error(f"Request failed: {e}")
            
            retries += 1
            time.sleep(self.delay * (2 ** retries))
            
        logger.error(f"Max retries exceeded for {url} {params}")
        return []

    def save_raw_batch(self, items, item_type):
        """Saves a batch of raw JSON responses."""
        if not items:
            return
            
        # Group by month for storage
        month_groups = {}
        for item in items:
            ts = item.get("created_utc")
            if not ts: continue
            month_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")
            if month_str not in month_groups:
                month_groups[month_str] = []
            month_groups[month_str].append(item)
            
        for month_str, month_items in month_groups.items():
            month_dir = self.raw_data_dir / month_str
            month_dir.mkdir(exist_ok=True)
            
            # Simple batch saving strategy (could be optimized)
            batch_id = int(time.time() * 1000)
            file_path = month_dir / f"{item_type}_batch_{batch_id}.json"
            
            with open(file_path, "w") as f:
                json.dump(month_items, f)

    def collect(self, max_batches=None):
        """Main collection loop."""
        subreddits = self.config['subreddits']
        end_dt = datetime.strptime(self.config['date_range']['end'], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_timestamp = int(end_dt.timestamp())
        
        for subreddit in subreddits:
            logger.info(f"Starting collection for r/{subreddit}")
            self._collect_items(subreddit, "posts", "posts/search", end_timestamp, max_batches)
            self._collect_items(subreddit, "comments", "comments/search", end_timestamp, max_batches)

    def _collect_items(self, subreddit, item_type, endpoint, end_timestamp, max_batches=None):
        current_ts = self._get_checkpoint(subreddit, item_type)
        batches_fetched = 0
        
        while current_ts < end_timestamp:
            if max_batches and batches_fetched >= max_batches:
                logger.info(f"Smoke test: max batches reached for {item_type}.")
                break
                
            params = {
                "subreddit": subreddit,
                "after": current_ts,
                "before": end_timestamp,
                "limit": self.limit,
                "sort": "asc" # Important: fetch chronologically
            }
            
            logger.info(f"Fetching {item_type} for r/{subreddit} after {current_ts}...")
            items = self._make_request(endpoint, params)
            
            if not items:
                logger.info(f"No more {item_type} found for r/{subreddit}")
                break
                
            self.save_raw_batch(items, item_type)
            batches_fetched += 1
            
            # Update timestamp to the newest item we received
            max_ts = max(item.get("created_utc", current_ts) for item in items)
            if max_ts == current_ts:
                max_ts += 1
                
            current_ts = max_ts
            self._save_checkpoint(subreddit, item_type, current_ts)
            
            logger.info(f"Saved {len(items)} {item_type}, new checkpoint: {current_ts}")
