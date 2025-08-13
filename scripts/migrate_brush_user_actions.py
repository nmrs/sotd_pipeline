#!/usr/bin/env python3
"""Migration script to convert brush user actions from list to dictionary format.

This script converts existing YAML files from the old format:
  brush_user_actions:
    - action: validated
      input_text: "Brush Name"
      ...

To the new format:
  brush_user_actions:
    "Brush Name":
      action: validated
      ...
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_file(file_path: Path, dry_run: bool = False) -> bool:
    """Migrate a single YAML file from list to dictionary format."""
    try:
        logger.info(f"Processing {file_path}")

        # Load the file
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "brush_user_actions" not in data:
            logger.warning(f"No brush_user_actions found in {file_path}")
            return True

        brush_actions = data["brush_user_actions"]

        # Check if already in new format (no wrapper key)
        if isinstance(brush_actions, dict) and "brush_user_actions" not in data:
            logger.info(f"{file_path} is already in new format, skipping")
            return True

        # Check if in old format (list) or wrapper format (dict with brush_user_actions key)
        if isinstance(brush_actions, list):
            # Old format: list of actions
            logger.info(f"Converting {len(brush_actions)} actions from list to dictionary format")
        elif isinstance(brush_actions, dict):
            # Wrapper format: dict with brush_user_actions key, need to remove wrapper
            logger.info(f"Converting {len(brush_actions)} actions from wrapper to direct format")
        else:
            logger.warning(f"Unexpected format in {file_path}, skipping")
            return True

        # Convert list to dictionary or remove wrapper
        new_brush_actions = {}

        if isinstance(brush_actions, list):
            # Old format: list of actions
            for action in brush_actions:
                if "input_text" not in action:
                    logger.warning(f"Action missing input_text: {action}")
                    continue

                input_text = action["input_text"]
                # Remove input_text from the action data since it's now the key
                action_data = action.copy()
                del action_data["input_text"]
                new_brush_actions[input_text] = action_data
        elif isinstance(brush_actions, dict):
            # Wrapper format: dict with brush_user_actions key, need to remove wrapper
            # The keys are already the input_text, just copy the data
            new_brush_actions = brush_actions.copy()
        else:
            logger.warning(f"Unexpected format in {file_path}, skipping")
            return True

        # Create new data structure - just the actions directly, no wrapper
        new_data = new_brush_actions

        if dry_run:
            logger.info(f"DRY RUN: Would convert {file_path}")
            logger.info(f"  Old format: {len(brush_actions)} list items")
            logger.info(f"  New format: {len(new_brush_actions)} dictionary keys")
            return True

        # Create backup
        backup_path = file_path.with_suffix(".yaml.backup")
        logger.info(f"Creating backup: {backup_path}")
        with open(backup_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

        # Write new format
        logger.info(f"Writing new format to {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(new_data, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

        logger.info(f"Successfully migrated {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False


def find_brush_user_actions_files(data_dir: Path) -> list[Path]:
    """Find all brush user actions YAML files in the data directory."""
    brush_actions_dir = data_dir / "learning" / "brush_user_actions"
    if not brush_actions_dir.exists():
        logger.warning(f"Directory not found: {brush_actions_dir}")
        return []

    yaml_files = list(brush_actions_dir.glob("*.yaml"))
    logger.info(f"Found {len(yaml_files)} YAML files in {brush_actions_dir}")
    return yaml_files


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate brush user actions from list to dictionary format"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to data directory (default: ./data)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    parser.add_argument("--file", type=Path, help="Migrate specific file instead of all files")

    args = parser.parse_args()

    if not args.data_dir.exists():
        logger.error(f"Data directory not found: {args.data_dir}")
        sys.exit(1)

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")

    if args.file:
        # Migrate specific file
        if not args.file.exists():
            logger.error(f"File not found: {args.file}")
            sys.exit(1)

        success = migrate_file(args.file, args.dry_run)
        if not success:
            sys.exit(1)
    else:
        # Migrate all files
        yaml_files = find_brush_user_actions_files(args.data_dir)
        if not yaml_files:
            logger.info("No files to migrate")
            return

        success_count = 0
        total_count = len(yaml_files)

        for yaml_file in yaml_files:
            if migrate_file(yaml_file, args.dry_run):
                success_count += 1

        logger.info(
            f"Migration complete: {success_count}/{total_count} files processed successfully"
        )

        if success_count < total_count:
            sys.exit(1)


if __name__ == "__main__":
    main()
