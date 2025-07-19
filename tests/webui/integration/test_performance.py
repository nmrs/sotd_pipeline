"""Performance tests for the filtered workflow."""

import tempfile
import time
from pathlib import Path

import pytest
import yaml

from sotd.utils.filtered_entries import FilteredEntriesManager


class TestPerformance:
    """Test performance characteristics of the filtered workflow."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_dir = temp_path / "data"
            data_dir.mkdir()

            # Create empty filtered entries file
            filtered_file = data_dir / "intentionally_unmatched.yaml"
            with open(filtered_file, "w") as f:
                yaml.dump(
                    {
                        "razor": {},
                        "brush": {},
                        "blade": {},
                        "soap": {},
                    },
                    f,
                )

            yield temp_path

    def test_large_dataset_performance(self, temp_data_dir):
        """Test performance with large datasets."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Add many entries to test performance
        start_time = time.time()
        for i in range(1000):
            manager.add_entry(
                "razor",
                f"Performance Test Razor {i}",
                f"comment_{i}",
                "data/comments/2025-01.json",
                "user",
            )
        add_time = time.time() - start_time

        # Should complete within reasonable time
        assert add_time < 10.0, f"Adding 1000 entries took {add_time:.2f}s, should be < 10s"

        # Test save performance
        start_time = time.time()
        manager.save()
        save_time = time.time() - start_time

        # Should save within reasonable time
        assert save_time < 5.0, f"Saving 1000 entries took {save_time:.2f}s, should be < 5s"

        # Test load performance
        manager2 = FilteredEntriesManager(filtered_file)
        start_time = time.time()
        manager2.load()
        load_time = time.time() - start_time

        # Should load within reasonable time
        assert load_time < 5.0, f"Loading 1000 entries took {load_time:.2f}s, should be < 5s"

        # Verify all entries were loaded
        assert manager2.is_filtered("razor", "Performance Test Razor 0")
        assert manager2.is_filtered("razor", "Performance Test Razor 999")

    def test_memory_usage_optimization(self, temp_data_dir):
        """Test memory usage optimization."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Add entries and monitor file size
        for i in range(500):
            manager.add_entry(
                "blade",
                f"Memory Test Blade {i}",
                f"comment_{i}",
                "data/comments/2025-01.json",
                "user",
            )

        manager.save()

        # Check file size is reasonable
        file_size = filtered_file.stat().st_size
        assert file_size < 512 * 1024, f"File size {file_size} bytes should be < 512KB"

        # Check memory usage by loading and checking structure
        manager2 = FilteredEntriesManager(filtered_file)
        manager2.load()

        # Verify data integrity
        assert len(manager2._data["blade"]) == 500
        for i in range(500):
            assert manager2.is_filtered("blade", f"Memory Test Blade {i}")

    def test_search_performance(self, temp_data_dir):
        """Test search performance in large datasets."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Add entries with different patterns
        for i in range(1000):
            manager.add_entry(
                "soap",
                f"Search Test Soap {i}",
                f"comment_{i}",
                "data/comments/2025-01.json",
                "user",
            )

        manager.save()

        # Test search performance
        start_time = time.time()
        for i in range(100):
            is_filtered = manager.is_filtered("soap", f"Search Test Soap {i}")
            assert is_filtered
        search_time = time.time() - start_time

        # Should complete searches quickly
        assert search_time < 1.0, f"100 searches took {search_time:.2f}s, should be < 1s"

    def test_bulk_operations_performance(self, temp_data_dir):
        """Test performance of bulk operations."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Test bulk add performance
        start_time = time.time()
        for category in ["razor", "brush", "blade", "soap"]:
            for i in range(100):
                manager.add_entry(
                    category,
                    f"Bulk Test {category} {i}",
                    f"comment_{category}_{i}",
                    "data/comments/2025-01.json",
                    "user",
                )
        bulk_add_time = time.time() - start_time

        # Should complete bulk operations within reasonable time
        assert (
            bulk_add_time < 15.0
        ), f"Bulk add of 400 entries took {bulk_add_time:.2f}s, should be < 15s"

        # Test bulk save performance
        start_time = time.time()
        manager.save()
        bulk_save_time = time.time() - start_time

        # Should save bulk operations quickly
        assert bulk_save_time < 5.0, f"Bulk save took {bulk_save_time:.2f}s, should be < 5s"

    def test_concurrent_access_performance(self, temp_data_dir):
        """Test performance under concurrent access."""
        import threading

        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        results = []

        def concurrent_operation(thread_id):
            try:
                manager = FilteredEntriesManager(filtered_file)
                manager.load()

                start_time = time.time()
                for i in range(50):
                    manager.add_entry(
                        "razor",
                        f"Concurrent Razor {thread_id}_{i}",
                        f"comment_{thread_id}_{i}",
                        "data/comments/2025-01.json",
                        "user",
                    )
                manager.save()
                operation_time = time.time() - start_time

                results.append((thread_id, "success", operation_time))
            except Exception as e:
                results.append((thread_id, f"error: {str(e)}", 0))

        # Start multiple threads
        threads = []
        for i in range(4):
            thread = threading.Thread(target=concurrent_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify performance under concurrent access
        success_count = sum(1 for _, result, _ in results if result == "success")
        assert success_count > 0, "At least some concurrent operations should succeed"

        # Check that operations completed within reasonable time
        for thread_id, result, operation_time in results:
            if result == "success":
                assert (
                    operation_time < 10.0
                ), f"Thread {thread_id} took {operation_time:.2f}s, should be < 10s"

    def test_file_size_optimization(self, temp_data_dir):
        """Test that file size remains optimized."""
        filtered_file = temp_data_dir / "data" / "intentionally_unmatched.yaml"
        manager = FilteredEntriesManager(filtered_file)
        manager.load()

        # Add entries and monitor file size growth
        initial_size = filtered_file.stat().st_size

        for i in range(100):
            manager.add_entry(
                "brush",
                f"Size Test Brush {i}",
                f"comment_{i}",
                "data/comments/2025-01.json",
                "user",
            )
            manager.save()

            current_size = filtered_file.stat().st_size
            # File size should grow reasonably (not exponentially)
            assert (
                current_size < initial_size + (i + 1) * 1000
            ), f"File size grew too much at iteration {i}"

        final_size = filtered_file.stat().st_size
        # Final file size should be reasonable
        assert final_size < 100 * 1024, f"Final file size {final_size} bytes should be < 100KB"
