"""Command-line interface for brush scoring optimization."""

import argparse
import logging
from pathlib import Path
from typing import Dict, Any

from .brush_scoring_optimizer import BrushScoringOptimizer
from .test_harness import BrushMatchingTestHarness


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load brush scoring configuration."""
    import yaml

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Optimize brush scoring configuration weights using machine learning"
    )
    parser.add_argument(
        "config_path",
        type=Path,
        help="Path to brush_scoring_config.yaml",
    )
    parser.add_argument(
        "correct_matches_path",
        type=Path,
        help="Path to correct_matches.yaml",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=100000,
        help="Maximum optimization iterations per strategy (default: 100000)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.1,
        help="Learning rate for gradient descent (default: 0.1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("🎯 Target: Maximize brush matching success rate")
    logger.info(f"📁 Config: {args.config_path}")
    logger.info(f"📁 Correct Matches: {args.correct_matches_path}")
    logger.info(f"🔄 Max Iterations: {args.max_iterations}")
    logger.info(f"📚 Learning Rate: {args.learning_rate}")

    # Load original configuration
    original_config = load_config(args.config_path)
    logger.info("✅ Configuration loaded successfully")

    # Create optimizer
    optimizer = BrushScoringOptimizer(
        config_path=args.config_path,
        correct_matches_path=args.correct_matches_path,
        max_iterations=args.max_iterations,
        learning_rate=args.learning_rate,
    )

    # Run round-robin optimization (default)
    logger.info("🚀 Starting round-robin strategy optimization...")
    optimized_weights, optimization_history = optimizer.optimize_weights_round_robin()

    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("OPTIMIZATION RESULTS")
    logger.info("=" * 80)

    # Show strategy-by-strategy results
    for progress in optimization_history:
        strategy = progress["strategy"]
        strategy_rate = progress["strategy_success_rate"]
        overall_rate = progress["overall_success_rate"]
        improvement = progress["improvement"]

        logger.info(f"\n📊 Strategy: {strategy}")
        logger.info(f"   Strategy Success Rate: {strategy_rate:.3f}")
        logger.info(f"   Overall Success Rate: {overall_rate:.3f}")
        logger.info(f"   Improvement: {improvement:.3f}")

    # Show final weights
    logger.info("\n" + "=" * 80)
    logger.info("FINAL OPTIMIZED WEIGHTS")
    logger.info("=" * 80)

    for weight_name, weight_value in optimized_weights.items():
        logger.info(f"{weight_name}: {weight_value:.6f}")

    # Create test harness for validation
    logger.info("\n🔍 Creating test harness for validation...")
    test_harness = BrushMatchingTestHarness(
        config_path=args.config_path,
    )

    # Create optimized config for validation
    optimized_config = optimizer._update_config_with_weights(optimized_weights)

    # Validate optimization results
    logger.info("🧪 Validating optimization results...")
    test_harness.validate_optimization_result(original_config, optimized_config)

    # Generate validation report
    logger.info("📋 Generating validation report...")
    validation_report = test_harness.generate_validation_report()

    print("\n" + "=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)
    print(validation_report)

    # Ask for user confirmation to apply optimized weights
    print("\n" + "=" * 80)
    print("APPLY OPTIMIZED WEIGHTS?")
    print("=" * 80)
    print("The optimization has completed. Would you like to:")
    print("1. Apply the optimized weights to your configuration file?")
    print("2. Save the optimized weights to a new file?")
    print("3. Just view the results without saving?")

    while True:
        choice = input("\nEnter your choice (1/2/3): ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("Please enter 1, 2, or 3.")

    if choice == "1":
        # Apply to original file
        import yaml

        with open(args.config_path, "w") as f:
            yaml.dump(original_config, f, default_flow_style=False, indent=2)
        logger.info(f"✅ Applied optimized weights to {args.config_path}")
        print(f"✅ Applied optimized weights to {args.config_path}")

    elif choice == "2":
        # Save to new file
        output_path = args.config_path.parent / f"{args.config_path.stem}_optimized.yaml"
        import yaml

        with open(output_path, "w") as f:
            yaml.dump(original_config, f, default_flow_style=False, indent=2)
        logger.info(f"✅ Saved optimized weights to {output_path}")
        print(f"✅ Saved optimized weights to {output_path}")

    else:
        logger.info("No changes applied - results displayed only")
        print("✅ No changes applied - results displayed only")

    logger.info("🎉 Optimization complete!")


if __name__ == "__main__":
    main()
