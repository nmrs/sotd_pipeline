"""Brush Scoring Optimization Engine.

This module implements PyTorch-based optimization for brush scoring weights
to maximize the success rate of brush matching against correct_matches.yaml.
Uses GPU acceleration when available (Apple Silicon MPS, CUDA, etc.).
"""

import copy
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import yaml

import torch
import torch.optim as optim

logger = logging.getLogger(__name__)


class BrushScoringOptimizer:
    """Optimizes brush scoring weights using gradient descent."""

    def __init__(self, config_path: Union[str, Path], correct_matches_path: Union[str, Path]):
        """Initialize the optimizer with configuration files.

        Args:
            config_path: Path to brush_scoring_config.yaml
            correct_matches_path: Path to correct_matches.yaml
        """
        self.config_path = Path(config_path)
        self.correct_matches_path = Path(correct_matches_path)

        # Load initial configuration
        self.original_config = self._load_config()
        self.current_config = copy.deepcopy(self.original_config)

        # Extract all numeric weights for optimization
        self.optimizable_weights = self._extract_optimizable_weights()
        self.weight_names = list(self.optimizable_weights.keys())

        # Optimization parameters
        self.learning_rate = 0.001  # Lower learning rate for Adam optimizer
        self.max_iterations = 100_000  # Increased to 100K iterations
        self.improvement_threshold = 0.0001  # 0.01% improvement threshold
        self.consecutive_no_improvement_limit = 100  # More patient convergence

        # PyTorch device setup
        self.device = self._setup_device()
        logger.info(f"Using device: {self.device}")

        # Convert weights to PyTorch tensors
        self.weight_tensors = self._create_weight_tensors()

        # Cache test cases to avoid reloading YAML file during optimization
        self._test_cases_cache = None
        self._load_test_cases()

        logger.info(f"Initialized optimizer with {len(self.weight_names)} optimizable weights")

    def _setup_device(self) -> torch.device:
        """Setup PyTorch device for optimal performance."""
        if torch.backends.mps.is_available():
            return torch.device("mps")  # Apple Silicon GPU
        elif torch.cuda.is_available():
            return torch.device("cuda")  # NVIDIA GPU
        else:
            return torch.device("cpu")  # CPU fallback

    def _create_weight_tensors(self) -> Dict[str, torch.Tensor]:
        """Convert weights to PyTorch tensors with requires_grad=True."""
        tensors = {}
        for weight_name, weight_value in self.optimizable_weights.items():
            tensor = torch.tensor(
                weight_value, dtype=torch.float32, device=self.device, requires_grad=True
            )
            tensors[weight_name] = tensor
        return tensors

    def _weights_to_dict(self) -> Dict[str, float]:
        """Convert PyTorch tensors back to dictionary."""
        return {name: tensor.item() for name, tensor in self.weight_tensors.items()}

    def _load_config(self) -> Dict[str, Any]:
        """Load the brush scoring configuration from YAML."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from {self.config_path}: {e}")

    def _extract_optimizable_weights(self) -> Dict[str, float]:
        """Extract all numeric weights from the configuration."""
        weights = {}

        def extract_weights(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (int, float)):
                        weights[current_key] = float(value)
                    elif isinstance(value, dict):
                        extract_weights(value, current_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_key = f"{prefix}[{i}]"
                    if isinstance(item, (int, float)):
                        weights[current_key] = float(item)
                    elif isinstance(item, dict):
                        extract_weights(item, current_key)

        extract_weights(self.original_config)
        return weights

    def _update_config_with_weights(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """Update the configuration with new weight values."""
        config = copy.deepcopy(self.original_config)

        def update_weights(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    if current_key in weights:
                        obj[key] = weights[current_key]
                    elif isinstance(value, dict):
                        update_weights(value, current_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_key = f"{prefix}[{i}]"
                    if current_key in weights:
                        obj[i] = weights[current_key]
                    elif isinstance(item, dict):
                        update_weights(item, current_key)

        update_weights(config)
        return config

    def evaluate_configuration(self, weights: Dict[str, float]) -> float:
        """Evaluate a weight configuration and return success rate.

        Args:
            weights: Dictionary of weight names to values

        Returns:
            Success rate as a float between 0.0 and 1.0
        """
        # Update the configuration with new weights
        updated_config = self._update_config_with_weights(weights)

        # Test the configuration against real SOTD data (not correct_matches.yaml)
        success_count = 0
        total_count = 0

        # Import here to avoid circular imports
        from sotd.match.brush_matcher import BrushMatcher

        # Create a temporary config file with the updated weights
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(updated_config, f)
            temp_config_path = Path(f.name)

        try:
            # Create brush matcher with the updated config and bypass correct_matches.yaml
            brush_matcher = BrushMatcher(
                config_path=temp_config_path,
                correct_matches_path=self.correct_matches_path,
                bypass_correct_matches=True,  # Skip correct_matches.yaml for optimization
            )

            # Use cached test cases to avoid reloading YAML file
            test_cases = self._get_test_cases()

            # Test each extracted test case
            for test_case in test_cases:
                total_count += 1

                # Test if this input produces the expected match structure
                result = brush_matcher.match(test_case["input"])
                if result and result.matched:
                    matched_data = result.matched

                    # Validate result structure matches expected format
                    if self._validate_match_structure(matched_data, test_case):
                        success_count += 1

                        # Log detailed results for debugging (but limit output)
                        if total_count <= 5:  # Only log first few for performance
                            test_type = test_case["type"]
                            logger.debug(
                                f"Test '{test_case['input']}' -> Success: {test_type} match"
                            )
                    else:
                        if total_count <= 5:
                            logger.debug(f"Test '{test_case['input']}' -> Failed: Wrong structure")
                else:
                    if total_count <= 5:
                        logger.debug(f"Test '{test_case['input']}' -> Failed: No match result")

            # Calculate success rate
            if total_count == 0:
                logger.warning("No test cases found in correct_matches.yaml")
                return 0.0

            success_rate = success_count / total_count
            logger.debug(f"Success rate: {success_count}/{total_count} = {success_rate:.3f}")
            return success_rate

        finally:
            # Clean up temporary config file
            temp_config_path.unlink(missing_ok=True)

    def _extract_test_cases(self, test_data: dict) -> list[dict]:
        """Extract test cases from the nested correct_matches.yaml structure.

        Args:
            test_data: Loaded YAML data from correct_matches.yaml

        Returns:
            List of test case dictionaries with input, type, and expected structure
        """
        test_cases = []

        # Extract complete brush test cases
        if "brush" in test_data:
            brush_data = test_data["brush"]
            for brand, brand_data in brush_data.items():
                if isinstance(brand_data, dict):
                    for model, patterns in brand_data.items():
                        if isinstance(patterns, list):
                            for pattern in patterns:
                                if isinstance(pattern, dict):
                                    # Dictionary with handle_match flag
                                    original_text = list(pattern.keys())[0]
                                else:
                                    # Simple string pattern
                                    original_text = pattern

                                test_cases.append(
                                    {
                                        "input": original_text,
                                        "type": "complete_brush",
                                        "expected_brand": brand,
                                        "expected_model": model,
                                    }
                                )

        # Extract composite brush test cases (from handle section)
        if "handle" in test_data:
            handle_data = test_data["handle"]
            for brand, brand_data in handle_data.items():
                if isinstance(brand_data, dict):
                    for model, patterns in brand_data.items():
                        if isinstance(patterns, list):
                            for pattern in patterns:
                                test_cases.append(
                                    {
                                        "input": pattern,
                                        "type": "composite_brush",
                                        "expected_handle_brand": brand,
                                        "expected_handle_model": model,
                                    }
                                )

        # Extract composite brush test cases (from knot section)
        if "knot" in test_data:
            knot_data = test_data["knot"]
            for brand, brand_data in knot_data.items():
                if isinstance(brand_data, dict):
                    for model, patterns in brand_data.items():
                        if isinstance(patterns, list):
                            for pattern in patterns:
                                test_cases.append(
                                    {
                                        "input": pattern,
                                        "type": "composite_brush",
                                        "expected_knot_brand": brand,
                                        "expected_knot_model": model,
                                    }
                                )

        return test_cases

    def _validate_match_structure(self, matched_data: dict, test_case: dict) -> bool:
        """Validate that the match result has the expected structure.

        Args:
            matched_data: The matched data from brush matcher
            test_case: The test case with expected structure

        Returns:
            True if structure matches expected, False otherwise
        """
        if test_case["type"] == "complete_brush":
            # Complete brush should have brand and model at top level
            brand = matched_data.get("brand")
            model = matched_data.get("model")

            # Check if we got the expected brand/model
            if brand and model:
                brand_match = brand.lower() == test_case["expected_brand"].lower()
                model_match = model.lower() == test_case["expected_model"].lower()
                return brand_match and model_match
            return False

        elif test_case["type"] == "composite_brush":
            # Composite brush should have handle and knot sections
            handle = matched_data.get("handle", {})
            knot = matched_data.get("knot", {})

            if not handle or not knot:
                return False

            # Check handle structure if expected
            if "expected_handle_brand" in test_case:
                handle_brand = handle.get("brand")
                handle_model = handle.get("model")
                if not (handle_brand and handle_model):
                    return False

                handle_brand_match = (
                    handle_brand.lower() == test_case["expected_handle_brand"].lower()
                )
                handle_model_match = (
                    handle_model.lower() == test_case["expected_handle_model"].lower()
                )
                if not (handle_brand_match and handle_model_match):
                    return False

            # Check knot structure if expected
            if "expected_knot_brand" in test_case:
                knot_brand = knot.get("brand")
                knot_model = knot.get("model")
                if not (knot_brand and knot_model):
                    return False
                if (
                    knot_brand.lower() != test_case["expected_knot_brand"].lower()
                    or knot_model.lower() != test_case["expected_knot_model"].lower()
                ):
                    return False

            return True

        return False

    def calculate_gradients(
        self, weights: Dict[str, float], base_success_rate: float
    ) -> Dict[str, float]:
        """Calculate gradients for each weight using finite differences.

        Args:
            weights: Current weight configuration
            base_success_rate: Success rate with current weights

        Returns:
            Dictionary mapping weight names to their gradients
        """
        gradients = {}
        epsilon = 0.01  # Small perturbation for finite difference

        for weight_name in self.weight_names:
            # Create perturbed weights
            perturbed_weights = weights.copy()
            perturbed_weights[weight_name] += epsilon

            # Evaluate perturbed configuration
            perturbed_success_rate = self.evaluate_configuration(perturbed_weights)

            # Calculate gradient using finite difference
            gradient = (perturbed_success_rate - base_success_rate) / epsilon
            gradients[weight_name] = gradient

            logger.debug(f"Gradient for {weight_name}: {gradient}")

        return gradients

    def optimize_weights(self) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """Run PyTorch-based optimization to maximize success rate.

        Returns:
            Tuple of (optimized_weights, optimization_history)
        """
        logger.info("Starting weight optimization using PyTorch with Adam optimizer")

        # Setup optimizer
        optimizer = optim.Adam(list(self.weight_tensors.values()), lr=self.learning_rate)

        optimization_history = []
        consecutive_no_improvement = 0
        best_success_rate = 0.0
        best_weights = self._weights_to_dict()

        for iteration in range(self.max_iterations):
            # Zero gradients
            optimizer.zero_grad()

            # Evaluate current configuration
            current_weights = self._weights_to_dict()
            current_success_rate = self.evaluate_configuration(current_weights)

            # Record progress
            progress = {
                "iteration": iteration,
                "success_rate": current_success_rate,
                "weights": current_weights.copy(),
                "improvement": current_success_rate - best_success_rate,
            }
            optimization_history.append(progress)

            # Log progress every 1000 iterations or on improvement
            if iteration % 1000 == 0 or current_success_rate > best_success_rate:
                logger.info(f"Iteration {iteration}: Success rate = {current_success_rate:.3f}")

            # Check for improvement
            if current_success_rate > best_success_rate:
                best_success_rate = current_success_rate
                best_weights = current_weights.copy()
                consecutive_no_improvement = 0

                logger.info(f"New best success rate: {best_success_rate:.3f}")

                # Check if we've reached 100%
                if best_success_rate >= 1.0:
                    logger.info("Reached 100% success rate - optimization complete")
                    break
            else:
                consecutive_no_improvement += 1

                # Check convergence criteria
                if consecutive_no_improvement >= self.consecutive_no_improvement_limit:
                    logger.info(
                        f"No improvement for {self.consecutive_no_improvement_limit} "
                        "iterations - stopping"
                    )
                    break

            # Calculate loss (negative success rate for minimization)
            loss = torch.tensor(1.0 - current_success_rate, requires_grad=True)

            # Backward pass (automatic differentiation)
            loss.backward()

            # Update weights using optimizer
            optimizer.step()

            # Ensure weights stay positive
            for tensor in self.weight_tensors.values():
                tensor.data.clamp_(min=0.0)

        logger.info(f"Optimization complete. Best success rate: {best_success_rate:.3f}")
        return best_weights, optimization_history

    def get_optimized_config(self, optimized_weights: Dict[str, float]) -> Dict[str, Any]:
        """Get the full configuration with optimized weights.

        Args:
            optimized_weights: Dictionary of optimized weight values

        Returns:
            Complete configuration dictionary with optimized weights
        """
        return self._update_config_with_weights(optimized_weights)

    def save_optimized_config(
        self, optimized_weights: Dict[str, float], output_path: Union[str, Path]
    ) -> None:
        """Save the optimized configuration to a file.

        Args:
            optimized_weights: Dictionary of optimized weight values
            output_path: Path where to save the optimized configuration
        """
        optimized_config = self.get_optimized_config(optimized_weights)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(optimized_config, f, default_flow_style=False, indent=2)
            logger.info(f"Saved optimized configuration to {output_path}")
        except Exception as e:
            raise ValueError(f"Failed to save optimized configuration: {e}")

    def get_weight_changes(
        self, optimized_weights: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Get a summary of weight changes from original to optimized.

        Args:
            optimized_weights: Dictionary of optimized weight values

        Returns:
            Dictionary mapping weight names to change information
        """
        changes = {}

        for weight_name in self.weight_names:
            original_value = self.optimizable_weights[weight_name]

            # Handle case where optimized_weights doesn't contain all weights
            if weight_name not in optimized_weights:
                # Use original value if not provided in optimized weights
                optimized_value = original_value
            else:
                optimized_value = optimized_weights[weight_name]

            change = optimized_value - original_value
            change_percent = (
                (change / original_value * 100) if original_value != 0 else float("inf")
            )

            changes[weight_name] = {
                "original": original_value,
                "optimized": optimized_value,
                "change": change,
                "change_percent": change_percent,
            }

        return changes

    def _test_single_match_with_matcher(
        self, example: str, brush_matcher, expected_brand: str, expected_model: str
    ) -> bool:
        """Test if a single example matches correctly using the brush matcher.

        Args:
            example: The brush string to test
            brush_matcher: BrushMatcher instance with updated config
            expected_brand: Expected brand from correct_matches.yaml
            expected_model: Expected model from correct_matches.yaml

        Returns:
            True if match is correct, False otherwise
        """
        try:
            # Use the brush matcher to test the example
            result = brush_matcher.match(example)

            if not result or not result.matched:
                return False

            # Check if the matched result matches our expectations
            matched_data = result.matched
            actual_brand = matched_data.get("brand")
            actual_model = matched_data.get("model")

            # Case-insensitive comparison (following match phase rules)
            return (
                actual_brand
                and actual_brand.lower() == expected_brand.lower()
                and actual_model
                and actual_model.lower() == expected_model.lower()
            )

        except Exception as e:
            logger.warning(f"Error testing match for '{example}': {e}")
            return False

    def _test_single_match(self, example: str, config: Dict[str, Any]) -> bool:
        """Legacy method for backward compatibility."""
        # This method is kept for backward compatibility but should not be used
        # The new _test_single_match_with_matcher method is preferred
        logger.warning("_test_single_match is deprecated, use _test_single_match_with_matcher")
        return False

    def _load_test_cases(self) -> None:
        """Load and cache test cases from correct_matches.yaml."""
        try:
            with open(self.correct_matches_path, "r", encoding="utf-8") as f:
                test_data = yaml.safe_load(f) or {}

            self._test_cases_cache = self._extract_test_cases(test_data)
            logger.info(
                f"Loaded {len(self._test_cases_cache)} test cases from correct_matches.yaml"
            )
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            self._test_cases_cache = []

    def _get_test_cases(self) -> list[dict]:
        """Get cached test cases, reloading if necessary."""
        if self._test_cases_cache is None:
            self._load_test_cases()
        return self._test_cases_cache or []
