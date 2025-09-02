"""
Strategy Dependency Manager Component.

This component manages dependencies between brush matching strategies and determines
optimal execution order based on dependency relationships.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set


class DependencyType(Enum):
    """Types of dependencies between strategies."""

    REQUIRES_SUCCESS = "requires_success"
    REQUIRES_FAILURE = "requires_failure"
    REQUIRES_ANY = "requires_any"
    REQUIRES_ALL = "requires_all"


@dataclass
class StrategyDependency:
    """Represents a dependency between two strategies."""

    dependent_strategy: str
    depends_on_strategy: str
    dependency_type: DependencyType

    def __eq__(self, other):
        if not isinstance(other, StrategyDependency):
            return False
        return (
            self.dependent_strategy == other.dependent_strategy
            and self.depends_on_strategy == other.depends_on_strategy
            and self.dependency_type == other.dependency_type
        )

    def __repr__(self):
        return (
            f"StrategyDependency(dependent_strategy='{self.dependent_strategy}', "
            f"depends_on_strategy='{self.depends_on_strategy}', "
            f"dependency_type={self.dependency_type.name})"
        )


class StrategyDependencyManager:
    """
    Manages dependencies between brush matching strategies.

    This component tracks dependencies between strategies and determines
    whether strategies can execute based on the results of their dependencies.
    """

    def __init__(self):
        """Initialize the dependency manager."""
        self.dependencies: List[StrategyDependency] = []
        # Graph for dependency checking: dependent_strategy -> set of depends_on_strategies
        self.dependency_graph: Dict[str, Set[str]] = {}
        # Graph for topological sort: depends_on_strategy -> set of dependent_strategies
        self.topological_graph: Dict[str, Set[str]] = {}

    def add_dependency(self, dependency: StrategyDependency) -> None:
        """
        Add a dependency between strategies.

        Args:
            dependency: StrategyDependency object defining the relationship
        """
        self.dependencies.append(dependency)

        # Update dependency graph for dependency checking
        # dependent_strategy -> set of depends_on_strategies
        dependent_strategy = dependency.dependent_strategy
        depends_on_strategy = dependency.depends_on_strategy

        if dependent_strategy not in self.dependency_graph:
            self.dependency_graph[dependent_strategy] = set()

        self.dependency_graph[dependent_strategy].add(depends_on_strategy)

        # Update topological graph for topological sort
        # depends_on_strategy -> set of dependent_strategies
        if depends_on_strategy not in self.topological_graph:
            self.topological_graph[depends_on_strategy] = set()

        self.topological_graph[depends_on_strategy].add(dependent_strategy)

    def can_execute_strategy(self, strategy_name: str, strategy_results: Dict[str, Any]) -> bool:
        """
        Check if a strategy can execute based on its dependencies.

        Args:
            strategy_name: Name of the strategy to check
            strategy_results: Dictionary of strategy results by strategy name

        Returns:
            True if the strategy can execute, False otherwise
        """
        # If strategy has no dependencies, it can always execute
        if strategy_name not in self.dependency_graph:
            return True

        # Group dependencies by type for proper handling
        dependencies_by_type = {}
        for dependency in self.dependencies:
            if dependency.dependent_strategy != strategy_name:
                continue

            if dependency.dependency_type not in dependencies_by_type:
                dependencies_by_type[dependency.dependency_type] = []
            dependencies_by_type[dependency.dependency_type].append(dependency)

        # Check each dependency type
        for dep_type, deps in dependencies_by_type.items():
            if dep_type in [DependencyType.REQUIRES_SUCCESS, DependencyType.REQUIRES_FAILURE]:
                # Single dependency check - all must be satisfied
                for dependency in deps:
                    if not self._check_single_dependency(dependency, strategy_results):
                        return False
            elif dep_type == DependencyType.REQUIRES_ANY:
                # At least one dependency must be satisfied
                if not self._check_requires_any_dependencies(deps, strategy_results):
                    return False
            elif dep_type == DependencyType.REQUIRES_ALL:
                # All dependencies must be satisfied
                if not self._check_requires_all_dependencies(deps, strategy_results):
                    return False

        return True

    def _check_single_dependency(
        self, dependency: StrategyDependency, strategy_results: Dict[str, Any]
    ) -> bool:
        """
        Check if a single dependency is satisfied.

        Args:
            dependency: The dependency to check
            strategy_results: Dictionary of strategy results

        Returns:
            True if dependency is satisfied, False otherwise
        """
        depends_on_strategy = dependency.depends_on_strategy

        # Skip if dependency strategy hasn't run yet
        if depends_on_strategy not in strategy_results:
            return False  # Consider unsatisfied if dependency hasn't run yet

        result = strategy_results[depends_on_strategy]
        return self._check_dependency_satisfaction(dependency, result)

    def _check_requires_any_dependencies(
        self, dependencies: List[StrategyDependency], strategy_results: Dict[str, Any]
    ) -> bool:
        """
        Check if at least one dependency from a list is satisfied.

        Args:
            dependencies: List of dependencies to check
            strategy_results: Dictionary of strategy results

        Returns:
            True if at least one dependency is satisfied, False otherwise
        """
        # Check if any dependencies have run and succeeded
        any_satisfied = False
        any_checked = False

        for dependency in dependencies:
            depends_on_strategy = dependency.depends_on_strategy
            if depends_on_strategy in strategy_results:
                any_checked = True
                if self._check_single_dependency(dependency, strategy_results):
                    any_satisfied = True
                    break

        # If no dependencies have been checked yet, allow execution
        if not any_checked:
            return True

        # If some dependencies have been checked, at least one must be satisfied
        return any_satisfied

    def _check_requires_all_dependencies(
        self, dependencies: List[StrategyDependency], strategy_results: Dict[str, Any]
    ) -> bool:
        """
        Check if all dependencies from a list are satisfied.

        Args:
            dependencies: List of dependencies to check
            strategy_results: Dictionary of strategy results

        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        # Check if all dependencies have run and succeeded
        for dependency in dependencies:
            if not self._check_single_dependency(dependency, strategy_results):
                return False

        return True

    def _check_dependency_satisfaction(self, dependency: StrategyDependency, result: Any) -> bool:
        """
        Check if a specific dependency is satisfied.

        Args:
            dependency: The dependency to check
            result: The result of the dependency strategy

        Returns:
            True if dependency is satisfied, False otherwise
        """
        # Determine if the dependency strategy succeeded or failed
        dependency_succeeded = (
            result is not None and hasattr(result, "matched") and result.matched is not None
        )

        if dependency.dependency_type == DependencyType.REQUIRES_SUCCESS:
            return dependency_succeeded
        elif dependency.dependency_type == DependencyType.REQUIRES_FAILURE:
            return not dependency_succeeded
        elif dependency.dependency_type == DependencyType.REQUIRES_ANY:
            # For REQUIRES_ANY, we check if this specific dependency succeeded
            return dependency_succeeded
        elif dependency.dependency_type == DependencyType.REQUIRES_ALL:
            # For REQUIRES_ALL, we check if this specific dependency succeeded
            return dependency_succeeded
        else:
            # Unknown dependency type
            return False

    def get_execution_order(self, strategy_names: List[str]) -> List[str]:
        """
        Get optimal execution order based on dependencies.

        Args:
            strategy_names: List of strategy names to order

        Returns:
            List of strategy names in optimal execution order

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Check for circular dependencies
        self._check_circular_dependencies(strategy_names)

        # Use topological sort to determine execution order
        return self._topological_sort(strategy_names)

    def _check_circular_dependencies(self, strategy_names: List[str]) -> None:
        """
        Check for circular dependencies in the strategy graph.

        Args:
            strategy_names: List of strategy names to check

        Raises:
            ValueError: If circular dependencies are detected
        """
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)

            if node in self.topological_graph:
                for neighbor in self.topological_graph[node]:
                    if neighbor in strategy_names:
                        if neighbor not in visited:
                            dfs(neighbor)
                        elif neighbor in rec_stack:
                            if neighbor == node:
                                raise ValueError(f"Self-dependency detected for strategy: {node}")
                            else:
                                raise ValueError(
                                    f"Circular dependency detected involving {node} and {neighbor}"
                                )

            rec_stack.remove(node)

        for strategy in strategy_names:
            if strategy not in visited:
                dfs(strategy)

    def _topological_sort(self, strategy_names: List[str]) -> List[str]:
        """
        Perform topological sort to determine execution order.

        Args:
            strategy_names: List of strategy names to sort

        Returns:
            List of strategy names in topological order
        """
        # Calculate in-degrees (how many strategies each strategy depends on)
        in_degree = {strategy: 0 for strategy in strategy_names}

        # Count incoming edges for each strategy
        # If A depends on B, then B has an incoming edge from A
        for strategy in strategy_names:
            if strategy in self.topological_graph:
                for dependent_strategy in self.topological_graph[strategy]:
                    if dependent_strategy in strategy_names:
                        in_degree[dependent_strategy] += 1

        # Find nodes with no incoming edges (can execute first)
        queue = [strategy for strategy in strategy_names if in_degree[strategy] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for all strategies that current depends on
            if current in self.topological_graph:
                for dependent_strategy in self.topological_graph[current]:
                    if dependent_strategy in strategy_names:
                        in_degree[dependent_strategy] -= 1
                        if in_degree[dependent_strategy] == 0:
                            queue.append(dependent_strategy)

        # Check if all nodes were processed
        if len(result) != len(strategy_names):
            raise ValueError("Circular dependency detected in topological sort")

        return result

    def get_blocked_strategies(self, strategy_results: Dict[str, Any]) -> List[str]:
        """
        Get list of strategies that are blocked by dependencies.

        Args:
            strategy_results: Dictionary of strategy results by strategy name

        Returns:
            List of strategy names that are currently blocked
        """
        blocked_strategies = []

        for strategy_name in self.dependency_graph.keys():
            if not self.can_execute_strategy(strategy_name, strategy_results):
                blocked_strategies.append(strategy_name)

        return blocked_strategies

    def get_dependency_status(self, strategy_name: str, strategy_results: Dict[str, Any]) -> Dict:
        """
        Get detailed dependency status for a strategy.

        Args:
            strategy_name: Name of the strategy to check
            strategy_results: Dictionary of strategy results by strategy name

        Returns:
            Dictionary with dependency status information
        """
        if strategy_name not in self.dependency_graph:
            return {
                "can_execute": True,
                "satisfied_dependencies": [],
                "unsatisfied_dependencies": [],
                "total_dependencies": 0,
            }

        satisfied_deps = []
        unsatisfied_deps = []

        for dependency in self.dependencies:
            if dependency.dependent_strategy != strategy_name:
                continue

            depends_on_strategy = dependency.depends_on_strategy

            if depends_on_strategy not in strategy_results:
                unsatisfied_deps.append(depends_on_strategy)
                continue

            result = strategy_results[depends_on_strategy]
            dependency_satisfied = self._check_dependency_satisfaction(dependency, result)

            if dependency_satisfied:
                satisfied_deps.append(depends_on_strategy)
            else:
                unsatisfied_deps.append(depends_on_strategy)

        return {
            "can_execute": len(unsatisfied_deps) == 0,
            "satisfied_dependencies": satisfied_deps,
            "unsatisfied_dependencies": unsatisfied_deps,
            "total_dependencies": len(satisfied_deps) + len(unsatisfied_deps),
        }
