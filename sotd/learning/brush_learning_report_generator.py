"""
Brush Learning Report Generator.

This module provides report generation capabilities for the brush learning system,
analyzing brush validation data and generating structured reports for ChatGPT analysis.
"""

from datetime import datetime
from typing import Any, Dict, List


class BrushLearningReportGenerator:
    """
    Generator for brush learning analysis reports.

    This class analyzes brush validation data and generates structured reports
    for different stages of ChatGPT analysis including strategy selection,
    modifier performance, and pattern discovery.
    """

    def __init__(self, validation_data: List[Dict[str, Any]]):
        """
        Initialize the report generator with validation data.

        Args:
            validation_data: List of brush validation records
        """
        self.validation_data = validation_data or []

    def generate_strategy_analysis_report(self) -> Dict[str, Any]:
        """
        Generate strategy selection analysis report.

        Analyzes which strategies are winning vs. losing, score distributions,
        and common patterns in overrides.

        Returns:
            Dictionary containing strategy analysis results
        """
        if not self.validation_data:
            return {
                "status": "no_data",
                "report_type": "strategy_analysis",
                "analysis_date": datetime.now().isoformat(),
                "system_info": {"system_type": "brush_scoring", "version": "1.0"},
                "strategy_performance": {},
                "win_loss_rates": {},
                "score_distributions": {},
                "override_patterns": {},
                "warnings": ["No validation data available for analysis"],
            }

        # Analyze strategy performance
        strategy_stats = self._analyze_strategy_performance()
        win_loss_rates = self._calculate_win_loss_rates()
        score_distributions = self._analyze_score_distributions()
        override_patterns = self._analyze_override_patterns()

        # Validate data quality and collect warnings
        warnings = self._validate_data_quality()

        return {
            "status": "success",
            "report_type": "strategy_analysis",
            "analysis_date": datetime.now().isoformat(),
            "system_info": {"system_type": "brush_scoring", "version": "1.0"},
            "strategy_performance": strategy_stats,
            "win_loss_rates": win_loss_rates,
            "score_distributions": score_distributions,
            "override_patterns": override_patterns,
            "warnings": warnings,
        }

    def generate_modifier_performance_report(self) -> Dict[str, Any]:
        """
        Generate modifier performance analysis report.

        Analyzes how well current modifiers are working and their effectiveness
        by strategy.

        Returns:
            Dictionary containing modifier performance analysis
        """
        if not self.validation_data:
            return {
                "status": "no_data",
                "report_type": "modifier_performance",
                "analysis_date": datetime.now().isoformat(),
                "system_info": {"system_type": "brush_scoring", "version": "1.0"},
                "modifier_effectiveness": {},
                "correlation_analysis": {},
                "weight_suggestions": {},
            }

        # Analyze modifier effectiveness
        modifier_effectiveness = self._analyze_modifier_effectiveness()
        correlation_analysis = self._analyze_modifier_correlations()
        weight_suggestions = self._generate_weight_suggestions()

        return {
            "status": "success",
            "report_type": "modifier_performance",
            "analysis_date": datetime.now().isoformat(),
            "system_info": {"system_type": "brush_scoring", "version": "1.0"},
            "modifier_effectiveness": modifier_effectiveness,
            "correlation_analysis": correlation_analysis,
            "weight_suggestions": weight_suggestions,
        }

    def generate_pattern_discovery_report(self) -> Dict[str, Any]:
        """
        Generate pattern discovery analysis report.

        Identifies new patterns that need modifiers and suggests new modifier
        functions based on override patterns.

        Returns:
            Dictionary containing pattern discovery analysis
        """
        if not self.validation_data:
            return {
                "status": "no_data",
                "report_type": "pattern_discovery",
                "analysis_date": datetime.now().isoformat(),
                "system_info": {"system_type": "brush_scoring", "version": "1.0"},
                "common_override_patterns": {},
                "text_characteristics": {},
                "suggested_modifiers": {},
            }

        # Analyze patterns in override cases
        override_patterns = self._identify_override_patterns()
        text_characteristics = self._analyze_text_characteristics()
        suggested_modifiers = self._suggest_new_modifiers()

        return {
            "status": "success",
            "report_type": "pattern_discovery",
            "analysis_date": datetime.now().isoformat(),
            "system_info": {"system_type": "brush_scoring", "version": "1.0"},
            "common_override_patterns": override_patterns,
            "text_characteristics": text_characteristics,
            "suggested_modifiers": suggested_modifiers,
        }

    def _analyze_strategy_performance(self) -> Dict[str, Any]:
        """Analyze performance statistics for each strategy."""
        strategy_stats = {}

        for record in self.validation_data:
            if not self._is_valid_record(record):
                continue

            # Get system choice strategy
            system_choice = record.get("system_choice", {})
            strategy_name = system_choice.get("strategy")

            if strategy_name:
                if strategy_name not in strategy_stats:
                    strategy_stats[strategy_name] = {
                        "total_selections": 0,
                        "validated_selections": 0,
                        "overridden_selections": 0,
                        "average_score": 0.0,
                        "score_sum": 0.0,
                    }

                stats = strategy_stats[strategy_name]
                stats["total_selections"] += 1

                # Track validation vs override
                action = record.get("action", "")
                if action == "validated":
                    stats["validated_selections"] += 1
                elif action == "overridden":
                    stats["overridden_selections"] += 1

                # Track scores
                score = system_choice.get("score", 0.0)
                if isinstance(score, (int, float)):
                    stats["score_sum"] += score
                    stats["average_score"] = stats["score_sum"] / stats["total_selections"]

            # Also track all strategies that were evaluated (from all_strategies)
            all_strategies = record.get("all_strategies", [])
            for strategy_result in all_strategies:
                strategy_name = strategy_result.get("strategy")
                if strategy_name and strategy_name not in strategy_stats:
                    strategy_stats[strategy_name] = {
                        "total_selections": 0,
                        "validated_selections": 0,
                        "overridden_selections": 0,
                        "average_score": 0.0,
                        "score_sum": 0.0,
                        "evaluated_count": 0,  # Track how many times this strategy was evaluated
                    }

                if strategy_name:
                    strategy_stats[strategy_name]["evaluated_count"] = (
                        strategy_stats[strategy_name].get("evaluated_count", 0) + 1
                    )

        return strategy_stats

    def _calculate_win_loss_rates(self) -> Dict[str, Any]:
        """Calculate win/loss rates for strategies."""
        win_loss = {}

        for strategy_name, stats in self._analyze_strategy_performance().items():
            total = stats["total_selections"]
            if total > 0:
                win_rate = stats["validated_selections"] / total * 100
                loss_rate = stats["overridden_selections"] / total * 100
                win_loss[strategy_name] = {
                    "win_rate": win_rate,
                    "loss_rate": loss_rate,
                    "total_selections": total,
                }

        return win_loss

    def _analyze_score_distributions(self) -> Dict[str, Any]:
        """Analyze score distributions for strategies."""
        distributions = {}

        for record in self.validation_data:
            if not self._is_valid_record(record):
                continue

            all_strategies = record.get("all_strategies", [])
            for strategy_result in all_strategies:
                strategy_name = strategy_result.get("strategy")
                score = strategy_result.get("score")

                if strategy_name and isinstance(score, (int, float)):
                    if strategy_name not in distributions:
                        distributions[strategy_name] = {
                            "scores": [],
                            "min_score": float("inf"),
                            "max_score": float("-inf"),
                            "avg_score": 0.0,
                        }

                    dist = distributions[strategy_name]
                    dist["scores"].append(score)
                    dist["min_score"] = min(dist["min_score"], score)
                    dist["max_score"] = max(dist["max_score"], score)
                    dist["avg_score"] = sum(dist["scores"]) / len(dist["scores"])

        return distributions

    def _analyze_override_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in override cases."""
        override_patterns = {
            "total_overrides": 0,
            "common_system_strategies": {},
            "common_user_strategies": {},
            "common_input_patterns": [],
        }

        override_cases = [r for r in self.validation_data if r.get("action") == "overridden"]
        override_patterns["total_overrides"] = len(override_cases)

        for record in override_cases:
            # Track system vs user strategy choices
            system_strategy = record.get("system_choice", {}).get("strategy")
            user_strategy = record.get("user_choice", {}).get("strategy")

            if system_strategy:
                if system_strategy not in override_patterns["common_system_strategies"]:
                    override_patterns["common_system_strategies"][system_strategy] = 0
                override_patterns["common_system_strategies"][system_strategy] += 1

            if user_strategy:
                if user_strategy not in override_patterns["common_user_strategies"]:
                    override_patterns["common_user_strategies"][user_strategy] = 0
                override_patterns["common_user_strategies"][user_strategy] += 1

        return override_patterns

    def _analyze_modifier_effectiveness(self) -> Dict[str, Any]:
        """Analyze effectiveness of current modifiers."""
        modifier_effectiveness = {}

        for record in self.validation_data:
            system_choice = record.get("system_choice", {})
            modifiers = system_choice.get("modifiers", {})
            action = record.get("action", "")

            for modifier_name, modifier_value in modifiers.items():
                if modifier_name not in modifier_effectiveness:
                    modifier_effectiveness[modifier_name] = {
                        "validated_count": 0,
                        "overridden_count": 0,
                        "total_count": 0,
                        "average_value": 0.0,
                        "value_sum": 0.0,
                    }

                stats = modifier_effectiveness[modifier_name]
                stats["total_count"] += 1

                if isinstance(modifier_value, (int, float)):
                    stats["value_sum"] += modifier_value
                    stats["average_value"] = stats["value_sum"] / stats["total_count"]

                if action == "validated":
                    stats["validated_count"] += 1
                elif action == "overridden":
                    stats["overridden_count"] += 1

        return modifier_effectiveness

    def _analyze_modifier_correlations(self) -> Dict[str, Any]:
        """Analyze correlations between modifiers and validation outcomes."""
        # Basic correlation analysis - can be enhanced later
        return {"note": "Basic correlation analysis - to be enhanced in future iterations"}

    def _generate_weight_suggestions(self) -> Dict[str, Any]:
        """Generate weight adjustment suggestions based on modifier effectiveness."""
        suggestions = {}
        modifier_effectiveness = self._analyze_modifier_effectiveness()

        for modifier_name, stats in modifier_effectiveness.items():
            total = stats["total_count"]
            if total > 0:
                validation_rate = stats["validated_count"] / total
                suggestion = {
                    "current_validation_rate": validation_rate,
                    "recommendation": "maintain" if validation_rate > 0.7 else "adjust",
                }
                if validation_rate < 0.5:
                    suggestion["suggested_action"] = "decrease_weight"
                elif validation_rate > 0.8:
                    suggestion["suggested_action"] = "increase_weight"

                suggestions[modifier_name] = suggestion

        return suggestions

    def _identify_override_patterns(self) -> Dict[str, Any]:
        """Identify common patterns in override cases."""
        override_patterns = {}
        override_cases = [r for r in self.validation_data if r.get("action") == "overridden"]

        # Analyze input text patterns
        input_patterns = {}
        for record in override_cases:
            input_text = record.get("input_text", "").lower()

            # Look for common keywords
            keywords = ["custom", "artisan", "handmade", "turned", "/", "w/", "with", "in"]
            for keyword in keywords:
                if keyword in input_text:
                    if keyword not in input_patterns:
                        input_patterns[keyword] = 0
                    input_patterns[keyword] += 1

        override_patterns["keyword_frequency"] = input_patterns
        override_patterns["total_override_cases"] = len(override_cases)

        return override_patterns

    def _analyze_text_characteristics(self) -> Dict[str, Any]:
        """Analyze text characteristics that correlate with correct/incorrect matches."""
        characteristics = {
            "delimiter_patterns": {},
            "word_count_patterns": {},
            "brand_patterns": {},
        }

        for record in self.validation_data:
            input_text = record.get("input_text", "")
            action = record.get("action", "")

            # Analyze delimiter patterns
            delimiters = ["/", "w/", "with", "in", "-", "+"]
            for delimiter in delimiters:
                if delimiter in input_text:
                    if delimiter not in characteristics["delimiter_patterns"]:
                        characteristics["delimiter_patterns"][delimiter] = {
                            "validated": 0,
                            "overridden": 0,
                        }

                    if action == "validated":
                        characteristics["delimiter_patterns"][delimiter]["validated"] += 1
                    elif action == "overridden":
                        characteristics["delimiter_patterns"][delimiter]["overridden"] += 1

        return characteristics

    def _suggest_new_modifiers(self) -> Dict[str, Any]:
        """Suggest new modifiers based on patterns found in override cases."""
        suggestions = {}
        override_patterns = self._identify_override_patterns()

        # Suggest modifiers based on frequent keywords in override cases
        keyword_freq = override_patterns.get("keyword_frequency", {})
        for keyword, count in keyword_freq.items():
            if count >= 2:  # If keyword appears in 2+ override cases
                suggestions[f"{keyword}_modifier"] = {
                    "pattern": keyword,
                    "frequency": count,
                    "suggested_weight": 10.0,
                    "description": f"Modifier to handle cases with '{keyword}' pattern",
                }

        return suggestions

    def _validate_data_quality(self) -> List[str]:
        """Validate data quality and return warnings."""
        warnings = []

        for i, record in enumerate(self.validation_data):
            if not self._is_valid_record(record):
                warnings.append(f"Record {i} has invalid structure")

        return warnings

    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """Check if a validation record has valid structure."""
        required_fields = ["input_text", "action"]
        return all(field in record for field in required_fields)
