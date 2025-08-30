"""Brush scoring optimization using PyTorch-based gradient descent.

This module provides tools for optimizing brush matching configuration weights
to maximize correct match success rate using machine learning techniques.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any

import torch
import torch.optim as optim
import yaml
from tqdm import tqdm

logger = logging.getLogger(__name__)


class BrushScoringOptimizer:
    """Optimizes brush scoring configuration weights using PyTorch gradient descent."""

    def __init__(
        self,
        config_path: Path,
        correct_matches_path: Path,
        max_iterations: int = 100000,
        learning_rate: float = 0.1,
        improvement_threshold: float = 0.0001,
        consecutive_no_improvement_limit: int = 25,
    ):
        """Initialize the optimizer.

        Args:
            config_path: Path to brush_scoring_config.yaml
            correct_matches_path: Path to correct_matches.yaml
            max_iterations: Maximum optimization iterations
            learning_rate: Learning rate for gradient descent
            improvement_threshold: Minimum improvement to continue
            consecutive_no_improvement_limit: Iterations without improvement before stopping
        """
        self.config_path = config_path
        self.correct_matches_path = correct_matches_path
        self.max_iterations = max_iterations
        self.learning_rate = learning_rate
        self.improvement_threshold = improvement_threshold
        self.consecutive_no_improvement_limit = consecutive_no_improvement_limit

        # Load configuration and extract weights
        self.config = self._load_config()
        self.weight_tensors = {}
        self.device = self._setup_device()
        self._create_weight_tensors()

        # Test case caching
        self._test_cases_cache = None

        # Strategy optimization order (highest priority first)
        self.strategy_order = [
            "known_brush",
            "known_split",
            "omega_semogue_brush",
            "zenith_brush",
            "other_brush",
            "automated_split",
            "full_input_component_matching",
            "handle_matching",
            "knot_matching",
        ]

    def _load_config(self) -> dict:
        """Load the brush scoring configuration."""
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _setup_device(self) -> torch.device:
        """Setup PyTorch device (MPS for Apple Silicon, CUDA for NVIDIA, CPU fallback)."""
        if torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("Using Apple Silicon MPS device")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info("Using CUDA device")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU device")
        return device

    def _create_weight_tensors(self):
        """Create PyTorch tensors for all numeric weights in the config."""

        def extract_weights(obj, prefix=""):
            """Recursively extract numeric weights from nested config."""
            weights = {}
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_prefix = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (int, float)):
                        weights[current_prefix] = torch.tensor(
                            float(value), requires_grad=True, device=self.device
                        )
                    elif isinstance(value, dict):
                        weights.update(extract_weights(value, current_prefix))
            return weights

        self.weight_tensors = extract_weights(self.config)
        logger.info(f"Created {len(self.weight_tensors)} weight tensors")

    def _weights_to_dict(self) -> Dict[str, float]:
        """Convert weight tensors back to dictionary."""
        return {name: tensor.item() for name, tensor in self.weight_tensors.items()}

    def _update_config_with_weights(self, weights: Dict[str, float]) -> dict:
        """Update configuration with new weight values."""
        updated_config = self.config.copy()

        def update_nested(obj, weight_dict):
            """Recursively update nested configuration with new weights."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, (int, float)):
                        weight_key = f"{key}"
                        if weight_key in weight_dict:
                            obj[key] = weight_dict[weight_key]
                    elif isinstance(value, dict):
                        update_nested(value, weight_dict)

        update_nested(updated_config, weights)
        return updated_config

    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from correct_matches.yaml."""
        with open(self.correct_matches_path, "r") as f:
            correct_matches = yaml.safe_load(f)

        test_cases = []

        # Extract brush test cases
        if "brush" in correct_matches:
            for brand, models in correct_matches["brush"].items():
                for model, entries in models.items():
                    for entry in entries:
                        test_case = {
                            "input": entry,
                            "expected_type": "complete",
                            "expected_brand": brand,
                            "expected_model": model,
                            "category": "Known Brush",
                            "difficulty": "Easy",
                        }
                        test_cases.append(test_case)

        # Extract handle test cases
        if "handle" in correct_matches:
            for brand, models in correct_matches["handle"].items():
                for model, entries in models.items():
                    for entry in entries:
                        test_case = {
                            "input": entry,
                            "expected_type": "composite",
                            "expected_component": "handle",
                            "expected_brand": brand,
                            "category": "Dual Component",
                            "difficulty": "Medium",
                        }
                        test_cases.append(test_case)

        # Extract knot test cases
        if "knot" in correct_matches:
            for brand, models in correct_matches["knot"].items():
                for model, entries in models.items():
                    for entry in entries:
                        test_case = {
                            "input": entry,
                            "expected_type": "composite",
                            "expected_component": "knot",
                            "expected_brand": brand,
                            "category": "Dual Component",
                            "difficulty": "Medium",
                        }
                        test_cases.append(test_case)

        logger.info(f"Loaded {len(test_cases)} test cases from correct_matches.yaml")
        return test_cases

    def _get_test_cases(self) -> List[Dict[str, Any]]:
        """Get cached test cases, loading if necessary."""
        if self._test_cases_cache is None:
            self._test_cases_cache = self._load_test_cases()
        return self._test_cases_cache

    def _validate_match_structure(self, matched_data: dict, test_case: dict) -> bool:
        """Validate that match result structure and content matches expected type."""
        if test_case["expected_type"] == "complete":
            # Complete brush should have brand and model
            # It may also have handle/knot sections (hybrid structure)
            if not ("brand" in matched_data and "model" in matched_data):
                return False

            # Validate that the brand and model actually match what's expected
            expected_brand = test_case.get("brand")
            expected_model = test_case.get("model")

            if expected_brand and expected_brand != matched_data.get("brand"):
                return False
            if expected_model and expected_model != matched_data.get("model"):
                return False

            return True

        elif test_case["expected_type"] == "composite":
            # Composite brush should have handle/knot components
            # It may also have brand/model at the top level (hybrid structure)
            has_components = (
                "handle_maker" in matched_data
                or "knot_brand" in matched_data
                or "handle" in matched_data
                or "knot" in matched_data
            )

            if not has_components:
                return False

            # Validate that the actual components match what's expected
            if test_case.get("category") == "handle":
                expected_maker = test_case.get("maker")
                expected_model = test_case.get("model")

                if expected_maker and expected_maker != matched_data.get("handle_maker"):
                    return False
                if expected_model and expected_model != matched_data.get("handle_model"):
                    return False

            elif test_case.get("category") == "knot":
                expected_brand = test_case.get("brand")
                expected_model = test_case.get("model")

                if expected_brand and expected_brand != matched_data.get("brand"):
                    return False
                if expected_model and expected_model != matched_data.get("model"):
                    return False

            return True

        return False

    def evaluate_configuration(self, weights: Dict[str, float]) -> float:
        """Evaluate a weight configuration and return success rate."""
        updated_config = self._update_config_with_weights(weights)
        success_count = 0
        total_count = 0

        from sotd.match.brush_matcher import BrushMatcher

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(updated_config, f)
            temp_config_path = Path(f.name)

        try:
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

            # Calculate success rate
            if total_count == 0:
                logger.warning("No test cases found in correct_matches.yaml")
                return 0.0

            success_rate = success_count / total_count
            return success_rate

        finally:
            # Clean up temporary config file
            temp_config_path.unlink(missing_ok=True)

    def _get_strategy_weights(self, strategy_name: str) -> Dict[str, torch.Tensor]:
        """Get weights associated with a specific strategy."""
        strategy_weights = {}
        for weight_name, tensor in self.weight_tensors.items():
            if strategy_name.lower() in weight_name.lower():
                strategy_weights[weight_name] = tensor
        return strategy_weights

    def _optimize_strategy(self, strategy_name: str) -> Tuple[float, Dict[str, float]]:
        """Optimize weights for a specific strategy."""
        logger.info(f"Optimizing strategy: {strategy_name}")

        # Get weights for this strategy
        strategy_weights = self._get_strategy_weights(strategy_name)
        if not strategy_weights:
            logger.warning(f"No weights found for strategy: {strategy_name}")
            return 0.0, {}

        logger.info(f"Found {len(strategy_weights)} weights for {strategy_name}")

        # Setup optimizer for this strategy only
        optimizer = optim.Adam(
            list(strategy_weights.values()),
            lr=self.learning_rate,
            betas=(0.9, 0.999),
            weight_decay=0.0001,
        )

        # Learning rate scheduler
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.1, patience=10
        )

        # Track optimization progress
        consecutive_no_improvement = 0
        best_success_rate = 0.0
        best_weights = {}

        # Main optimization loop for this strategy
        pbar = tqdm(range(self.max_iterations), desc=f"Optimizing {strategy_name}")
        for iteration in pbar:
            # Zero gradients
            optimizer.zero_grad()

            # Evaluate current configuration
            current_weights = self._weights_to_dict()
            current_success_rate = self.evaluate_configuration(current_weights)

            # Update progress bar
            desc = f"{strategy_name}: {current_success_rate:.3f} | Best: {best_success_rate:.3f}"
            pbar.set_description(desc)

            # Check for improvement
            if current_success_rate > best_success_rate:
                best_success_rate = current_success_rate
                best_weights = current_weights.copy()
                consecutive_no_improvement = 0

                # Update progress bar with new best
                desc = f"{strategy_name}: {current_success_rate:.3f} ✨"
                pbar.set_description(desc)

                # Check if we've reached 100%
                if best_success_rate >= 1.0:
                    pbar.set_description(f"{strategy_name}: 🎉 100% Success Rate!")
                    break
            else:
                consecutive_no_improvement += 1

                # Check convergence criteria
                if consecutive_no_improvement >= self.consecutive_no_improvement_limit:
                    # Try random perturbation to escape local maximum
                    logger.info(
                        f"🔄 No improvement for {strategy_name} - applying random perturbation..."
                    )
                    for tensor in strategy_weights.values():
                        noise = torch.randn_like(tensor) * 10.0  # Much bigger jumps
                        tensor.data += noise
                        tensor.data.clamp_(min=0.0)
                    consecutive_no_improvement = 0
                    pbar.set_description(f"{strategy_name}: 🔄 Random perturbation applied")

                    # If still stuck after perturbation, try random restart
                    if consecutive_no_improvement >= self.consecutive_no_improvement_limit * 2:
                        logger.info(
                            f"🔄 Still stuck for {strategy_name} - applying random restart..."
                        )
                        for tensor in strategy_weights.values():
                            random_weight = torch.rand_like(tensor) * 200.0  # Wider range
                            tensor.data = random_weight
                        consecutive_no_improvement = 0
                        pbar.set_description(f"{strategy_name}: 🔄 Random restart applied")

                        # If still stuck, try BIG jumps
                        if consecutive_no_improvement >= self.consecutive_no_improvement_limit * 3:
                            logger.info(
                                f"🚀 Still stuck for {strategy_name} - applying BIG jumps..."
                            )
                            for tensor in strategy_weights.values():
                                big_jump = torch.rand_like(tensor) * 1000.0
                                tensor.data = big_jump
                            consecutive_no_improvement = 0
                            pbar.set_description(f"{strategy_name}: 🚀 BIG jumps applied")
                        else:
                            break

            # Calculate loss (negative success rate for minimization)
            loss = torch.tensor(1.0 - current_success_rate, requires_grad=True)

            # Backward pass
            loss.backward()

            # Update weights using optimizer
            optimizer.step()

            # Step the scheduler
            scheduler.step(current_success_rate)

            # Ensure weights stay positive
            for tensor in strategy_weights.values():
                tensor.data.clamp_(min=0.0)

        logger.info(
            f"Strategy {strategy_name} optimization complete. Best success rate: {best_success_rate:.3f}"
        )
        return best_success_rate, best_weights

    def optimize_weights_round_robin(self) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """Run round-robin strategy optimization to maximize success rate.

        This approach cycles through strategies, restarting from the beginning
        whenever any strategy shows improvement, since strategies interact.

        Returns:
            Tuple of (optimized_weights, optimization_history)
        """
        logger.info("Starting round-robin strategy optimization")

        optimization_history = []
        current_weights = self._weights_to_dict()
        overall_best_success_rate = 0.0
        overall_best_weights = current_weights.copy()

        # Track which strategies have been optimized in this round
        strategies_this_round = set()
        round_number = 1

        while True:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Starting optimization round {round_number}")
            logger.info(f"{'=' * 60}")

            round_improved = False
            strategies_this_round.clear()

            # Optimize each strategy in priority order
            for strategy_name in self.strategy_order:
                if strategy_name in strategies_this_round:
                    continue  # Skip if already optimized this round

                logger.info(f"\n--- Optimizing strategy: {strategy_name} ---")

                # Get current overall success rate
                current_success_rate = self.evaluate_configuration(current_weights)
                logger.info(f"Current overall success rate: {current_success_rate:.3f}")

                # Optimize this strategy
                strategy_best_rate, strategy_best_weights = self._optimize_strategy(strategy_name)
                strategies_this_round.add(strategy_name)

                # Update current weights with optimized strategy weights
                current_weights.update(strategy_best_weights)

                # Evaluate new overall success rate
                new_overall_rate = self.evaluate_configuration(current_weights)
                improvement = new_overall_rate - overall_best_success_rate

                logger.info(f"Strategy {strategy_name} optimization complete:")
                logger.info(f"  Strategy success rate: {strategy_best_rate:.3f}")
                logger.info(f"  New overall success rate: {new_overall_rate:.3f}")
                logger.info(f"  Overall improvement: {improvement:.3f}")

                # Record progress
                progress = {
                    "round": round_number,
                    "strategy": strategy_name,
                    "strategy_success_rate": strategy_best_rate,
                    "overall_success_rate": new_overall_rate,
                    "improvement": improvement,
                    "weights": current_weights.copy(),
                }
                optimization_history.append(progress)

                # Check if we've reached 100%
                if new_overall_rate >= 1.0:
                    logger.info("🎉 100% Success Rate achieved!")
                    return overall_best_weights, optimization_history

                # If this strategy improved the overall result, mark round as improved
                if improvement > 0:
                    round_improved = True
                    overall_best_success_rate = new_overall_rate
                    overall_best_weights = current_weights.copy()
                    logger.info(
                        f"🎉 New overall best success rate: {overall_best_success_rate:.3f}"
                    )

                    # Continue with this round to see if other strategies can improve further
                    continue

                # If no improvement from this strategy, continue to next
                logger.info(f"No improvement from {strategy_name}, continuing...")

            # Round complete - check if we should continue
            if not round_improved:
                logger.info(f"\nRound {round_number} complete with no improvements.")
                logger.info("All strategies have been optimized without improvement.")
                break

            logger.info(f"\nRound {round_number} complete with improvements!")
            logger.info("Starting new round to see if other strategies can improve further...")
            round_number += 1

            # Optional: Add some randomization to avoid getting stuck in patterns
            if round_number > 3:
                # After 3 rounds, randomly shuffle strategy order to explore different paths
                import random

                random.shuffle(self.strategy_order)
                logger.info("Randomizing strategy order to explore different optimization paths...")

        logger.info(
            f"\nRound-robin optimization complete. Final success rate: {overall_best_success_rate:.3f}"
        )
        logger.info(f"Total rounds completed: {round_number}")
        return overall_best_weights, optimization_history

    def optimize_weights_sequential(self) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """Run sequential strategy optimization to maximize success rate.

        Returns:
            Tuple of (optimized_weights, optimization_history)
        """
        logger.info("Starting sequential strategy optimization")

        optimization_history = []
        current_weights = self._weights_to_dict()
        overall_best_success_rate = 0.0
        overall_best_weights = current_weights.copy()

        # Optimize each strategy in priority order
        for strategy_name in self.strategy_order:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Starting optimization of strategy: {strategy_name}")
            logger.info(f"{'=' * 60}")

            # Get current overall success rate
            current_success_rate = self.evaluate_configuration(current_weights)
            logger.info(f"Current overall success rate: {current_success_rate:.3f}")

            # Optimize this strategy
            strategy_best_rate, strategy_best_weights = self._optimize_strategy(strategy_name)

            # Update current weights with optimized strategy weights
            current_weights.update(strategy_best_weights)

            # Evaluate new overall success rate
            new_overall_rate = self.evaluate_configuration(current_weights)
            improvement = new_overall_rate - overall_best_success_rate

            logger.info(f"Strategy {strategy_name} optimization complete:")
            logger.info(f"  Strategy success rate: {strategy_best_rate:.3f}")
            logger.info(f"  New overall success rate: {new_overall_rate:.3f}")
            logger.info(f"  Overall improvement: {improvement:.3f}")

            # Record progress
            progress = {
                "strategy": strategy_name,
                "strategy_success_rate": strategy_best_rate,
                "overall_success_rate": new_overall_rate,
                "improvement": improvement,
                "weights": current_weights.copy(),
            }
            optimization_history.append(progress)

            # Update overall best if improved
            if new_overall_rate > overall_best_success_rate:
                overall_best_success_rate = new_overall_rate
                overall_best_weights = current_weights.copy()
                logger.info(f"🎉 New overall best success rate: {overall_best_success_rate:.3f}")

                # Check if we've reached 100%
                if overall_best_success_rate >= 1.0:
                    logger.info("🎉 100% Success Rate achieved!")
                    break

        logger.info(
            f"\nSequential optimization complete. Final success rate: {overall_best_success_rate:.3f}"
        )
        return overall_best_weights, optimization_history

    def optimize_weights(self) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """Legacy method - now calls round-robin optimization by default."""
        return self.optimize_weights_round_robin()
