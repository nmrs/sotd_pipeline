#!/usr/bin/env python3
"""Queue manager for async correct matches operations."""

import json
import logging
import random
import string
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

logger = logging.getLogger(__name__)


class QueueManager:
    """Manages async queue for correct matches operations."""

    def __init__(self, correct_matches_path: Path):
        """
        Initialize queue manager.

        Args:
            correct_matches_path: Path to correct_matches directory
        """
        self.correct_matches_path = correct_matches_path
        self.queue_file = correct_matches_path / ".queue.jsonl"
        self.status_file = correct_matches_path / ".status.json"
        self.lock_file = correct_matches_path / ".queue.lock"
        self._lock_timeout = 300  # 5 minutes max lock time
        self._processing = False
        self._stop_event = threading.Event()

    def _generate_operation_id(self) -> str:
        """Generate unique operation ID."""
        timestamp = int(time.time() * 1000)
        random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"op_{timestamp}_{random_suffix}"

    def add_operation(self, operation_type: str, field: str, matches: List[Dict[str, Any]]) -> str:
        """
        Add operation to queue file.

        Args:
            operation_type: Type of operation ("mark_correct" or "remove_correct")
            field: Field name (e.g., "soap", "razor")
            matches: List of matches to process

        Returns:
            operation_id: Unique identifier for this operation
        """
        operation_id = self._generate_operation_id()
        operation = {
            "operation_id": operation_id,
            "type": operation_type,
            "field": field,
            "matches": matches,
            "timestamp": time.time(),
            "status": "pending",
        }

        # Ensure directory exists
        self.correct_matches_path.mkdir(parents=True, exist_ok=True)

        # Append to queue file (atomic append)
        try:
            with self.queue_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(operation) + "\n")
            logger.info(f"Added operation {operation_id} to queue: {operation_type} for {field}")
        except Exception as e:
            logger.error(f"Failed to add operation to queue: {e}")
            raise

        # Initialize status
        self._update_status(operation_id, "pending", 0.0, "Operation queued")

        return operation_id

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status for an operation.

        Checks live status file first, then archive files if not found.
        This handles cases where operations have been cleaned up from live status
        but the frontend is still polling.

        Args:
            operation_id: Operation ID to check (format: op_TIMESTAMP_RANDOM)

        Returns:
            Status dictionary or None if not found
        """
        # Check live status file first
        if self.status_file.exists():
            try:
                with self.status_file.open("r", encoding="utf-8") as f:
                    status_data = json.load(f)
                if operation_id in status_data:
                    return status_data[operation_id]
            except Exception as e:
                logger.error(f"Failed to read status file: {e}")

        # If not found in live status, check archive files
        # Extract timestamp from operation_id to determine which archive to check
        try:
            # operation_id format: op_1768002684007_2bo3k1wh
            # Extract timestamp (milliseconds)
            parts = operation_id.split("_")
            if len(parts) >= 2 and parts[0] == "op":
                timestamp_ms = int(parts[1])
                timestamp = timestamp_ms / 1000.0  # Convert to seconds
                operation_date = datetime.fromtimestamp(timestamp)

                # Check archive file for this month
                archive_file = self._get_archive_file_path(operation_date)
                if archive_file.exists():
                    try:
                        with archive_file.open("r", encoding="utf-8") as f:
                            archive_data = json.load(f)
                        return archive_data.get(operation_id)
                    except Exception as e:
                        logger.error(f"Failed to read archive file {archive_file.name}: {e}")
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse timestamp from operation_id {operation_id}: {e}")
            # Fallback: check recent archive files (current month and previous month)
            # This handles edge cases where timestamp parsing fails
            for months_back in range(2):
                check_date = datetime.now().replace(day=1)
                for _ in range(months_back):
                    # Go back one month
                    if check_date.month == 1:
                        check_date = check_date.replace(year=check_date.year - 1, month=12)
                    else:
                        check_date = check_date.replace(month=check_date.month - 1)

                archive_file = self._get_archive_file_path(check_date)
                if archive_file.exists():
                    try:
                        with archive_file.open("r", encoding="utf-8") as f:
                            archive_data = json.load(f)
                        if operation_id in archive_data:
                            return archive_data[operation_id]
                    except Exception as e:
                        logger.error(f"Failed to read archive file {archive_file.name}: {e}")

        return None

    def _update_status(
        self,
        operation_id: str,
        status: str,
        progress: float,
        message: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update status for an operation.

        Args:
            operation_id: Operation ID
            status: Status ("pending", "processing", "completed", "failed")
            progress: Progress (0.0 to 1.0)
            message: Status message
            result: Optional result data
        """
        # Load existing status
        status_data = {}
        if self.status_file.exists():
            try:
                with self.status_file.open("r", encoding="utf-8") as f:
                    status_data = json.load(f)
            except Exception:
                status_data = {}

        # Update status
        status_entry = {
            "status": status,
            "progress": progress,
            "message": message,
            "updated_at": time.time(),
        }

        if status == "processing" and "started_at" not in status_data.get(operation_id, {}):
            status_entry["started_at"] = time.time()
        elif status in ("completed", "failed"):
            status_entry["completed_at"] = time.time()
            if result:
                status_entry["result"] = result

        # If operation is completed or failed, archive it but keep in live status briefly
        # This allows the frontend to get the final status before we remove it
        if status in ("completed", "failed"):
            # Archive the completed operation immediately
            self._archive_completed_operation(operation_id, status_entry)
            # Keep in live status for a grace period to allow frontend to get final status
            # The frontend stops polling once it sees completed/failed, but we keep it
            # briefly to avoid 404 errors during the transition
            status_data[operation_id] = status_entry
        else:
            # Update live status for pending/processing operations
            status_data[operation_id] = status_entry

        # Save status file atomically (only pending/processing operations)
        temp_file = self.status_file.with_suffix(".tmp")
        try:
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
            temp_file.replace(self.status_file)
        except Exception as e:
            logger.error(f"Failed to update status file: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def _get_archive_file_path(self, date: datetime) -> Path:
        """
        Get archive file path for a given date (monthly archives).

        Args:
            date: Date to get archive file for

        Returns:
            Path to archive file (e.g., .status.archive.2025-01.json)
        """
        date_str = date.strftime("%Y-%m")
        return self.correct_matches_path / f".status.archive.{date_str}.json"

    def _archive_completed_operation(self, operation_id: str, status_entry: Dict[str, Any]) -> None:
        """
        Archive a completed operation to monthly archive file.

        Uses the completion date to determine which monthly archive file to use.

        Args:
            operation_id: Operation ID
            status_entry: Status entry dictionary
        """
        # Get completion date from status entry
        completed_at = status_entry.get("completed_at")
        if not completed_at:
            # Fallback to updated_at if completed_at not available
            completed_at = status_entry.get("updated_at", time.time())

        # Convert timestamp to datetime
        completion_date = datetime.fromtimestamp(completed_at)

        # Get archive file path for this month
        archive_file = self._get_archive_file_path(completion_date)

        # Load existing archive
        archive_data = {}
        if archive_file.exists():
            try:
                with archive_file.open("r", encoding="utf-8") as f:
                    archive_data = json.load(f)
            except Exception:
                archive_data = {}

        # Add operation to archive
        archive_data[operation_id] = status_entry

        # Save archive file atomically
        temp_file = archive_file.with_suffix(".tmp")
        try:
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(archive_data, f, indent=2)
            temp_file.replace(archive_file)
            logger.debug(f"Archived operation {operation_id} to {archive_file.name}")
        except Exception as e:
            logger.error(f"Failed to archive operation {operation_id}: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def _acquire_lock(self) -> bool:
        """
        Acquire lock file for queue processing.

        Returns:
            True if lock acquired, False otherwise
        """
        if self.lock_file.exists():
            # Check if lock is stale (older than timeout)
            lock_age = time.time() - self.lock_file.stat().st_mtime
            if lock_age > self._lock_timeout:
                logger.warning(f"Removing stale lock file (age: {lock_age:.1f}s)")
                self.lock_file.unlink()
            else:
                return False

        # Create lock file
        try:
            self.lock_file.touch()
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def _release_lock(self) -> None:
        """Release lock file."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")

    def _read_queue(self) -> List[Dict[str, Any]]:
        """
        Read all pending operations from queue file.

        Returns:
            List of operation dictionaries
        """
        if not self.queue_file.exists():
            return []

        operations = []
        try:
            with self.queue_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        operation = json.loads(line)
                        if operation.get("status") == "pending":
                            operations.append(operation)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in queue file: {line[:50]}... Error: {e}")
                        continue
        except Exception as e:
            logger.error(f"Failed to read queue file: {e}")
            return []

        return operations

    def _remove_operation_from_queue(self, operation_id: str) -> None:
        """
        Remove completed operation from queue file.

        Args:
            operation_id: Operation ID to remove
        """
        if not self.queue_file.exists():
            return

        # Read all lines, filter out the completed operation
        lines = []
        try:
            with self.queue_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        operation = json.loads(line)
                        if operation.get("operation_id") != operation_id:
                            lines.append(line)
                    except json.JSONDecodeError:
                        # Keep invalid lines (don't lose data)
                        lines.append(line)
                        continue

            # Write back filtered lines
            with self.queue_file.open("w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")
        except Exception as e:
            logger.error(f"Failed to remove operation from queue: {e}")

    def _process_operation(self, operation: Dict[str, Any]) -> bool:
        """
        Process a single operation.

        Args:
            operation: Operation dictionary

        Returns:
            True if successful, False otherwise
        """
        operation_id = operation["operation_id"]
        operation_type = operation["type"]
        field = operation["field"]
        matches = operation["matches"]

        try:
            # Update status to processing
            self._update_status(
                operation_id, "processing", 0.1, f"Processing {len(matches)} matches..."
            )

            # Import here to avoid circular dependencies
            from rich.console import Console
            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager

            console = Console()
            manager = CorrectMatchesManager(console, self.correct_matches_path)

            # Load only the affected field (optimization)
            # For now, we still load all fields, but this can be optimized later
            manager.load_correct_matches()

            marked_count = 0
            errors = []

            # Process each match
            for i, match in enumerate(matches):
                try:
                    original = match.get("original", "")
                    matched = match.get("matched", {})

                    if not original or not matched:
                        errors.append(f"Invalid match data: {match}")
                        continue

                    # Update progress
                    progress = 0.2 + (i / len(matches)) * 0.6  # 20% to 80%
                    self._update_status(
                        operation_id,
                        "processing",
                        progress,
                        f"Processing match {i + 1}/{len(matches)}...",
                    )

                    # Prepare match data
                    if field == "blade" and "format" in matched:
                        match_data_to_save = {
                            "original": original,
                            "matched": matched,
                            "field": field,
                        }
                    else:
                        match_data_to_save = {
                            "original": original,
                            "matched": matched,
                            "field": field,
                        }

                    # Mark or remove match
                    match_key = manager.create_match_key(field, original, matched)

                    if operation_type == "mark_correct":
                        manager.mark_match_as_correct(match_key, match_data_to_save)
                        marked_count += 1
                    elif operation_type == "remove_correct":
                        # Use the manager's remove_match method
                        if manager.remove_match(field, original, matched):
                            marked_count += 1
                        else:
                            errors.append(f"Match not found: {original}")

                except Exception as e:
                    errors.append(f"Error processing match {match}: {e}")
                    logger.error(f"Error processing match in operation {operation_id}: {e}")

            # Save to file
            if marked_count > 0:
                self._update_status(operation_id, "processing", 0.9, "Saving changes to file...")
                manager.save_correct_matches()

            # Update status to completed
            result = {"marked_count": marked_count, "errors": errors}
            self._update_status(
                operation_id,
                "completed",
                1.0,
                f"Completed: {marked_count} matches processed",
                result,
            )

            # Remove from queue
            self._remove_operation_from_queue(operation_id)

            logger.info(f"Operation {operation_id} completed: {marked_count} matches processed")
            return True

        except Exception as e:
            logger.error(f"Error processing operation {operation_id}: {e}", exc_info=True)
            self._update_status(
                operation_id,
                "failed",
                0.0,
                f"Error: {str(e)}",
                {"error": str(e)},
            )
            # Don't remove from queue on failure - allow retry
            return False

    def _cleanup_old_completed_operations(self) -> None:
        """
        Remove completed/failed operations from live status that are older than grace period.

        This runs periodically to clean up operations that have been completed for a while,
        giving the frontend time to poll and get the final status.
        """
        GRACE_PERIOD_SECONDS = 10  # Keep completed operations for 10 seconds after completion

        if not self.status_file.exists():
            return

        try:
            with self.status_file.open("r", encoding="utf-8") as f:
                status_data = json.load(f)
        except Exception:
            return

        current_time = time.time()
        removed_count = 0

        # Find completed/failed operations older than grace period
        operations_to_remove = []
        for operation_id, status_entry in status_data.items():
            if status_entry.get("status") in ("completed", "failed"):
                completed_at = status_entry.get("completed_at")
                if completed_at and (current_time - completed_at) > GRACE_PERIOD_SECONDS:
                    operations_to_remove.append(operation_id)

        # Remove old completed operations
        if operations_to_remove:
            for operation_id in operations_to_remove:
                del status_data[operation_id]
                removed_count += 1

            # Save updated status file
            temp_file = self.status_file.with_suffix(".tmp")
            try:
                with temp_file.open("w", encoding="utf-8") as f:
                    json.dump(status_data, f, indent=2)
                temp_file.replace(self.status_file)
                if removed_count > 0:
                    logger.debug(
                        f"Cleaned up {removed_count} old completed operations from live status"
                    )
            except Exception as e:
                logger.error(f"Failed to cleanup old operations: {e}")
                if temp_file.exists():
                    temp_file.unlink()

    def process_queue(self) -> None:
        """Process all pending operations in queue."""
        if self._processing:
            logger.debug("Queue processing already in progress")
            return

        if not self._acquire_lock():
            logger.debug("Could not acquire lock, skipping queue processing")
            return

        self._processing = True
        try:
            # Cleanup old completed operations before processing new ones
            self._cleanup_old_completed_operations()

            operations = self._read_queue()
            if not operations:
                return

            logger.info(f"Processing {len(operations)} queued operations")

            for operation in operations:
                if self._stop_event.is_set():
                    logger.info("Stop event set, stopping queue processing")
                    break

                self._process_operation(operation)

        finally:
            self._processing = False
            self._release_lock()

    def start_background_worker(self) -> None:
        """Start background thread to continuously process queue."""

        def worker_loop():
            logger.info("Background queue worker started")
            while not self._stop_event.is_set():
                try:
                    self.process_queue()
                except Exception as e:
                    logger.error(f"Error in queue worker: {e}", exc_info=True)

                # Sleep before next check (1-2 seconds)
                self._stop_event.wait(1.5)

            logger.info("Background queue worker stopped")

        thread = threading.Thread(target=worker_loop, daemon=True, name="QueueWorker")
        thread.start()
        logger.info("Background queue worker thread started")

    def stop_background_worker(self) -> None:
        """Stop background worker thread."""
        self._stop_event.set()
        logger.info("Background queue worker stop requested")
