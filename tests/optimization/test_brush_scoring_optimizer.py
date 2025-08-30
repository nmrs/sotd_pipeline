"""Tests for the brush scoring optimizer."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

import torch
import yaml

from sotd.optimization.brush_scoring_optimizer import BrushScoringOptimizer


@pytest.fixture
def sample_config():
    """Sample brush scoring configuration for testing."""
    return {
        "brush_scoring_weights": {
            "base_strategies": {"known_brush": 80.0, "automated_split": 60.0, "known_split": 90.0},
            "strategy_modifiers": {
                "automated_split": {"multiple_brands": 10.0, "high_confidence": 15.0}
            },
        }
    }


@pytest.fixture
def sample_correct_matches():
    """Sample correct matches for testing."""
    return {"brush": {"Test Brand": {"Test Model": ["test brush 1", "test brush 2"]}}}


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_correct_matches_file(sample_correct_matches):
    """Create a temporary correct matches file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_correct_matches, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


class TestBrushScoringOptimizer:
    """Test the BrushScoringOptimizer class."""

    def test_initialization(self, temp_config_file, temp_correct_matches_file):
        """Test optimizer initialization."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        assert optimizer.config_path == temp_config_file
        assert optimizer.correct_matches_path == temp_correct_matches_file
        assert optimizer.max_iterations == 100_000
        assert optimizer.learning_rate == 0.1  # Actual default value in implementation
        assert len(optimizer.optimizable_weights) > 0
        assert len(optimizer.weight_names) > 0

    def test_device_setup(self, temp_config_file, temp_correct_matches_file):
        """Test PyTorch device setup."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Should detect available device
        assert optimizer.device in [torch.device("mps"), torch.device("cpu")]

        # Should create weight tensors on the correct device
        for tensor in optimizer.weight_tensors.values():
            assert tensor.device.type == optimizer.device.type
            assert tensor.requires_grad

    def test_weight_extraction(self, temp_config_file, temp_correct_matches_file):
        """Test extraction of optimizable weights from config."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Should extract all numeric values
        expected_weights = {
            "brush_scoring_weights.base_strategies.known_brush": 80.0,
            "brush_scoring_weights.base_strategies.automated_split": 60.0,
            "brush_scoring_weights.base_strategies.known_split": 90.0,
            "brush_scoring_weights.strategy_modifiers.automated_split.multiple_brands": 10.0,
            "brush_scoring_weights.strategy_modifiers.automated_split.high_confidence": 15.0,
        }

        for weight_name, expected_value in expected_weights.items():
            assert weight_name in optimizer.optimizable_weights
            assert optimizer.optimizable_weights[weight_name] == expected_value

    def test_weight_tensor_creation(self, temp_config_file, temp_correct_matches_file):
        """Test creation of PyTorch weight tensors."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Should create tensors for all weights
        assert len(optimizer.weight_tensors) == len(optimizer.optimizable_weights)

        for weight_name, tensor in optimizer.weight_tensors.items():
            assert isinstance(tensor, torch.Tensor)
            assert tensor.requires_grad
            assert tensor.device.type == optimizer.device.type
            assert tensor.dtype == torch.float32

    def test_weights_to_dict_conversion(self, temp_config_file, temp_correct_matches_file):
        """Test conversion from PyTorch tensors back to dictionary."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Convert tensors back to dict
        weights_dict = optimizer._weights_to_dict()

        # Should have same keys and values
        assert set(weights_dict.keys()) == set(optimizer.optimizable_weights.keys())

        for weight_name in optimizer.optimizable_weights:
            assert weights_dict[weight_name] == optimizer.optimizable_weights[weight_name]

    @patch("sotd.optimization.brush_scoring_optimizer.BrushScoringOptimizer.evaluate_configuration")
    def test_optimization_with_mock_evaluation(
        self, mock_evaluate, temp_config_file, temp_correct_matches_file
    ):
        """Test optimization process with mocked evaluation."""
        # Create a sequence of values that will be returned
        values = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        value_index = [0]  # Use list to make it mutable in closure

        def mock_evaluation_side_effect(*args, **kwargs):
            if value_index[0] < len(values):
                result = values[value_index[0]]
                value_index[0] += 1
                return result
            else:
                return 1.0  # Default return value after sequence is exhausted

        mock_evaluate.side_effect = mock_evaluation_side_effect

        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Run optimization
        optimized_weights, history = optimizer.optimize_weights()

        # Should complete optimization
        assert len(history) > 0
        assert optimized_weights is not None

        # Should have called evaluation multiple times
        assert mock_evaluate.call_count > 1

    def test_config_update_with_weights(self, temp_config_file, temp_correct_matches_file):
        """Test updating configuration with new weight values."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Create test weights
        test_weights = {
            "brush_scoring_weights.base_strategies.known_brush": 85.0,
            "brush_scoring_weights.base_strategies.automated_split": 65.0,
        }

        # Update config
        updated_config = optimizer._update_config_with_weights(test_weights)

        # Should have updated values
        assert updated_config["brush_scoring_weights"]["base_strategies"]["known_brush"] == 85.0
        assert updated_config["brush_scoring_weights"]["base_strategies"]["automated_split"] == 65.0

        # Should preserve other values
        assert updated_config["brush_scoring_weights"]["base_strategies"]["known_split"] == 90.0

    def test_save_optimized_config(self, temp_config_file, temp_correct_matches_file):
        """Test saving optimized configuration to file."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Create test weights
        test_weights = {"brush_scoring_weights.base_strategies.known_brush": 85.0}

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_output = Path(f.name)

        try:
            optimizer.save_optimized_config(test_weights, temp_output)

            # Should have created file
            assert temp_output.exists()

            # Should contain updated values
            with open(temp_output, "r") as f:
                saved_config = yaml.safe_load(f)

            assert saved_config["brush_scoring_weights"]["base_strategies"]["known_brush"] == 85.0

        finally:
            temp_output.unlink(missing_ok=True)

    def test_weight_changes_calculation(self, temp_config_file, temp_correct_matches_file):
        """Test calculation of weight changes from original to optimized."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Create test optimized weights
        test_weights = {
            "brush_scoring_weights.base_strategies.known_brush": 85.0,
            "brush_scoring_weights.base_strategies.automated_split": 65.0,
        }

        # Calculate changes
        changes = optimizer.get_weight_changes(test_weights)

        # Should have change information for each weight
        assert "brush_scoring_weights.base_strategies.known_brush" in changes
        assert "brush_scoring_weights.base_strategies.automated_split" in changes

        # Check specific change calculations
        known_brush_changes = changes["brush_scoring_weights.base_strategies.known_brush"]
        assert known_brush_changes["original"] == 80.0
        assert known_brush_changes["optimized"] == 85.0
        assert known_brush_changes["change"] == 5.0
        assert known_brush_changes["change_percent"] == 6.25

    def test_error_handling_invalid_config_path(self):
        """Test error handling for invalid config path."""
        with pytest.raises(FileNotFoundError, match="No such file or directory"):
            BrushScoringOptimizer(Path("nonexistent_file.yaml"), Path("nonexistent_matches.yaml"))

    def test_optimization_convergence_criteria(self, temp_config_file, temp_correct_matches_file):
        """Test optimization convergence criteria."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Should have reasonable convergence parameters
        assert optimizer.max_iterations == 100_000
        assert optimizer.improvement_threshold == 0.0001
        assert optimizer.consecutive_no_improvement_limit == 25  # Actual default value

    def test_gpu_acceleration_detection(self, temp_config_file, temp_correct_matches_file):
        """Test GPU acceleration detection."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Should detect available device
        device = optimizer.device

        # On Apple Silicon, should prefer MPS
        if torch.backends.mps.is_available():
            assert device == torch.device("mps")
        else:
            assert device == torch.device("cpu")

    def test_optimizer_setup(self, temp_config_file, temp_correct_matches_file):
        """Test PyTorch optimizer setup."""
        optimizer = BrushScoringOptimizer(temp_config_file, temp_correct_matches_file)

        # Should create Adam optimizer with correct learning rate
        # Note: This is tested indirectly through the optimization process
        assert optimizer.learning_rate == 0.1
        assert len(optimizer.weight_tensors) > 0
