import logging
import pandas as pd
from pathlib import Path
from src.utils import get_project_root, setup_logging

logger = setup_logging("qa")

class QAAgent:
    def __init__(self, config):
        self.config = config
        self.processed_dir = get_project_root() / "data" / "processed"
        self.reports_dir = get_project_root() / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_qa(self):
        logger.info("Starting QA checks...")
        
        posts_path = self.processed_dir / "posts.csv"
        comments_path = self.processed_dir / "comments.csv"
        
        report = []
        report.append("# Data Quality Assurance Report\n")
        
        if not posts_path.exists():
            report.append("- **ERROR**: posts.csv not found.\n")
        else:
            df_posts = pd.read_csv(posts_path)
            report.append("## Posts QA\n")
            report.append(f"- Total posts: {len(df_posts)}\n")
            report.append(f"- Unique post IDs: {df_posts['post_id'].nunique()}\n")
            report.append(f"- Missing bodies: {df_posts['body'].isna().sum()}\n")
            if 'author_hash' in df_posts.columns:
                report.append(f"- Pseudonymized: Yes\n")
            else:
                report.append(f"- Pseudonymized: **NO**\n")
                
            report.append("\n### Posts by Subreddit\n")
            for sub, count in df_posts['subreddit'].value_counts().items():
                report.append(f"- r/{sub}: {count}\n")
                
        if not comments_path.exists():
            report.append("\n- **ERROR**: comments.csv not found.\n")
        else:
            df_comments = pd.read_csv(comments_path)
            report.append("\n## Comments QA\n")
            report.append(f"- Total comments: {len(df_comments)}\n")
            report.append(f"- Unique comment IDs: {df_comments['comment_id'].nunique()}\n")
            report.append(f"- Missing bodies: {df_comments['body'].isna().sum()}\n")
            if 'author_hash' in df_comments.columns:
                report.append(f"- Pseudonymized: Yes\n")
            else:
                report.append(f"- Pseudonymized: **NO**\n")

            if posts_path.exists():
                post_ids = set(df_posts['post_id'])
                orphans = df_comments[~df_comments['post_id'].isin(post_ids)]
                report.append(f"- Orphan comments (post not in dataset): {len(orphans)}\n")

        report_file = self.reports_dir / "QA_REPORT.md"
        with open(report_file, "w") as f:
            f.writelines(report)
            
        logger.info(f"QA report generated at {report_file}")
