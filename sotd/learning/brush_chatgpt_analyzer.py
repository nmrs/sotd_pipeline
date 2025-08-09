"""
Brush ChatGPT Analyzer.

This module provides ChatGPT integration for brush learning analysis,
generating structured prompts and processing ChatGPT responses for
suggestions on strategy weights, modifiers, and pattern discovery.
"""

import json
from typing import Any, Dict, Optional, Union


class BrushChatGPTAnalyzer:
    """
    ChatGPT integration for brush learning analysis.

    This class generates structured prompts for different analysis stages
    and processes ChatGPT responses to provide actionable suggestions for
    improving the brush matching scoring system.
    """

    def __init__(self, api_key: Optional[str]):
        """
        Initialize the ChatGPT analyzer.

        Args:
            api_key: OpenAI API key for ChatGPT integration, or None for testing
        """
        self.api_key = api_key

    def analyze_strategy_selection(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze strategy selection performance using ChatGPT.

        Stage 1: Strategy Selection Analysis
        Focus: Which strategies are winning vs. losing
        Task: Analyze which strategies are performing well/poorly and suggest
              base strategy weight adjustments

        Args:
            report: Strategy analysis report from BrushLearningReportGenerator

        Returns:
            Dictionary containing weight adjustments and reasoning
        """
        if not self._validate_report(report):
            return {
                "error": "Invalid or empty report provided",
                "analysis_type": "strategy_selection",
            }

        if not self.api_key:
            return {
                "warning": "No API key provided - running in mock mode",
                "analysis_type": "strategy_selection",
                "weight_adjustments": {},
                "reasoning": "Mock analysis - no actual ChatGPT call made",
            }

        try:
            # Generate structured prompt for strategy analysis
            prompt = self._generate_strategy_analysis_prompt(report)

            # Call ChatGPT
            response = self._call_chatgpt(prompt)

            # Parse and return results
            return self._parse_strategy_analysis_response(response)

        except Exception as e:
            return {
                "error": f"ChatGPT analysis failed: {str(e)}",
                "analysis_type": "strategy_selection",
            }

    def analyze_modifier_performance(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze modifier performance using ChatGPT.

        Stage 2: Modifier Performance Analysis
        Focus: How well current modifiers are working
        Task: Analyze modifier effectiveness and suggest weight adjustments
              for existing modifiers

        Args:
            report: Modifier performance report from BrushLearningReportGenerator

        Returns:
            Dictionary containing modifier adjustments and reasoning
        """
        if not self._validate_report(report):
            return {
                "error": "Invalid or empty report provided",
                "analysis_type": "modifier_performance",
            }

        if not self.api_key:
            return {
                "warning": "No API key provided - running in mock mode",
                "analysis_type": "modifier_performance",
                "modifier_adjustments": {},
                "reasoning": "Mock analysis - no actual ChatGPT call made",
            }

        try:
            # Generate structured prompt for modifier analysis
            prompt = self._generate_modifier_performance_prompt(report)

            # Call ChatGPT
            response = self._call_chatgpt(prompt)

            # Parse and return results
            return self._parse_modifier_performance_response(response)

        except Exception as e:
            return {
                "error": f"ChatGPT analysis failed: {str(e)}",
                "analysis_type": "modifier_performance",
            }

    def analyze_pattern_discovery(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pattern discovery using ChatGPT.

        Stage 3: Pattern Discovery Analysis
        Focus: Finding new patterns that need modifiers
        Task: Identify new patterns that need modifiers and suggest new
              modifier functions

        Args:
            report: Pattern discovery report from BrushLearningReportGenerator

        Returns:
            Dictionary containing suggested new modifiers and reasoning
        """
        if not self._validate_report(report):
            return {
                "error": "Invalid or empty report provided",
                "analysis_type": "pattern_discovery",
            }

        if not self.api_key:
            return {
                "warning": "No API key provided - running in mock mode",
                "analysis_type": "pattern_discovery",
                "suggested_new_modifiers": [],
                "reasoning": "Mock analysis - no actual ChatGPT call made",
            }

        try:
            # Generate structured prompt for pattern discovery
            prompt = self._generate_pattern_discovery_prompt(report)

            # Call ChatGPT
            response = self._call_chatgpt(prompt)

            # Parse and return results
            return self._parse_pattern_discovery_response(response)

        except Exception as e:
            return {
                "error": f"ChatGPT analysis failed: {str(e)}",
                "analysis_type": "pattern_discovery",
            }

    def _validate_report(self, report: Dict[str, Any]) -> bool:
        """
        Validate that the report has the expected structure.

        Args:
            report: Report dictionary to validate

        Returns:
            True if report is valid, False otherwise
        """
        if not isinstance(report, dict):
            return False

        # Check for basic report structure
        if not report:
            return False

        # Report should have some analysis data
        has_data = any(
            key in report
            for key in [
                "strategy_performance",
                "modifier_effectiveness",
                "common_override_patterns",
            ]
        )

        return has_data

    def _generate_strategy_analysis_prompt(self, report: Dict[str, Any]) -> str:
        """
        Generate structured prompt for strategy selection analysis.

        Args:
            report: Strategy analysis report

        Returns:
            Formatted prompt string for ChatGPT
        """
        system_info = report.get("system_info", {})
        strategy_performance = report.get("strategy_performance", {})
        win_loss_rates = report.get("win_loss_rates", {})

        prompt = f"""You are an expert brush matching system analyst. I need your help analyzing strategy performance for a brush scoring system.

SYSTEM CONTEXT:
- System Type: {system_info.get("system_type", "brush_scoring")}
- System Version: {system_info.get("version", "1.0")}
- Analysis Type: Strategy Selection Performance

CURRENT STRATEGY PERFORMANCE DATA:
"""

        for strategy, stats in strategy_performance.items():
            win_loss = win_loss_rates.get(strategy, {})
            prompt += f"""
Strategy: {strategy}
- Total Selections: {stats.get("total_selections", 0)}
- Validated Selections: {stats.get("validated_selections", 0)}
- Overridden Selections: {stats.get("overridden_selections", 0)}
- Win Rate: {win_loss.get("win_rate", 0):.1f}%
- Loss Rate: {win_loss.get("loss_rate", 0):.1f}%
- Average Score: {stats.get("average_score", 0):.1f}
"""

        prompt += """
TASK: Analyze the strategy performance data and provide weight adjustment recommendations.

Please respond in the following JSON format:
{
    "weight_adjustments": {
        "strategy_name": new_weight_value,
        // Suggest weight changes based on performance
    },
    "reasoning": "Detailed explanation of your analysis and recommendations"
}

GUIDELINES:
- Strategies with higher win rates should generally have higher weights
- Consider both selection frequency and validation success
- Provide clear reasoning for each adjustment
- Focus on actionable improvements to the scoring system
"""

        return prompt

    def _generate_modifier_performance_prompt(self, report: Dict[str, Any]) -> str:
        """
        Generate structured prompt for modifier performance analysis.

        Args:
            report: Modifier performance report

        Returns:
            Formatted prompt string for ChatGPT
        """
        system_info = report.get("system_info", {})
        modifier_effectiveness = report.get("modifier_effectiveness", {})

        prompt = f"""You are an expert brush matching system analyst. I need your help analyzing modifier performance for a brush scoring system.

SYSTEM CONTEXT:
- System Type: {system_info.get("system_type", "brush_scoring")}
- System Version: {system_info.get("version", "1.0")}
- Analysis Type: Modifier Performance Analysis

CURRENT MODIFIER EFFECTIVENESS DATA:
"""

        for modifier, stats in modifier_effectiveness.items():
            total = stats.get("total_count", 1)
            validation_rate = (stats.get("validated_count", 0) / total) * 100 if total > 0 else 0

            prompt += f"""
Modifier: {modifier}
- Total Applications: {total}
- Validated Count: {stats.get("validated_count", 0)}
- Overridden Count: {stats.get("overridden_count", 0)}
- Validation Rate: {validation_rate:.1f}%
- Average Value: {stats.get("average_value", 0):.2f}
"""

        prompt += """
TASK: Analyze the modifier effectiveness data and provide adjustment recommendations.

Please respond in the following JSON format:
{
    "modifier_adjustments": {
        "modifier_name": adjustment_value,
        // Positive values increase weight, negative values decrease
    },
    "reasoning": "Detailed explanation of your analysis and recommendations"
}

GUIDELINES:
- Modifiers with high validation rates should be enhanced
- Modifiers with low validation rates should be reduced or refined
- Consider both frequency of use and effectiveness
- Provide clear reasoning for each adjustment
"""

        return prompt

    def _generate_pattern_discovery_prompt(self, report: Dict[str, Any]) -> str:
        """
        Generate structured prompt for pattern discovery analysis.

        Args:
            report: Pattern discovery report

        Returns:
            Formatted prompt string for ChatGPT
        """
        system_info = report.get("system_info", {})
        override_patterns = report.get("common_override_patterns", {})
        text_characteristics = report.get("text_characteristics", {})

        prompt = f"""You are an expert brush matching system analyst. I need your help discovering new patterns for a brush scoring system.

SYSTEM CONTEXT:
- System Type: {system_info.get("system_type", "brush_scoring")}
- System Version: {system_info.get("version", "1.0")}
- Analysis Type: Pattern Discovery Analysis

OVERRIDE PATTERN DATA:
Total Override Cases: {override_patterns.get("total_override_cases", 0)}

Keyword Frequency in Overrides:
"""

        keyword_freq = override_patterns.get("keyword_frequency", {})
        for keyword, freq in keyword_freq.items():
            prompt += f"- '{keyword}': {freq} occurrences\n"

        prompt += """
TEXT CHARACTERISTICS:
"""

        delimiter_patterns = text_characteristics.get("delimiter_patterns", {})
        for delimiter, stats in delimiter_patterns.items():
            validated = stats.get("validated", 0)
            overridden = stats.get("overridden", 0)
            total = validated + overridden
            override_rate = (overridden / total * 100) if total > 0 else 0
            prompt += f"- Delimiter '{delimiter}': {override_rate:.1f}% override rate ({overridden}/{total})\n"

        prompt += """
TASK: Based on the pattern analysis, suggest new modifiers that could improve matching accuracy.

Please respond in the following JSON format:
{
    "suggested_new_modifiers": [
        {
            "name": "modifier_name",
            "function_name": "_modifier_function_name",
            "pattern": "regex_pattern_or_keyword",
            "logic": "Brief description of detection logic",
            "suggested_weights": {
                "strategy_name": weight_value
            },
            "test_cases": [
                "example input text 1",
                "example input text 2"
            ]
        }
    ],
    "reasoning": "Detailed explanation of pattern analysis and recommendations"
}

GUIDELINES:
- Focus on patterns that appear frequently in override cases
- Suggest modifiers that can detect semantic meaning (custom, artisan, etc.)
- Provide realistic weight suggestions based on pattern importance
- Include test cases that demonstrate the pattern
- Consider both positive and negative weight adjustments
"""

        return prompt

    def _call_chatgpt(self, prompt: str) -> Union[Dict[str, Any], str]:
        """
        Make API call to ChatGPT.

        Args:
            prompt: Formatted prompt string

        Returns:
            ChatGPT response (parsed if JSON, raw string otherwise)
        """
        # For now, this is a mock implementation
        # In real implementation, this would use OpenAI API
        # This allows tests to pass and provides a foundation for real integration

        if not self.api_key:
            raise Exception("No API key provided")

        # Mock response based on prompt content
        if "strategy" in prompt.lower():
            return {
                "weight_adjustments": {"known_brush": 85.0, "unified": 45.0},
                "reasoning": "Mock strategy analysis response",
            }
        elif "modifier" in prompt.lower():
            return {
                "modifier_adjustments": {"multiple_brands": -5.0, "fiber_words": 5.0},
                "reasoning": "Mock modifier analysis response",
            }
        elif "pattern" in prompt.lower():
            return {
                "suggested_new_modifiers": [
                    {
                        "name": "custom_handle",
                        "function_name": "_modifier_custom_handle",
                        "pattern": "custom|artisan|handmade",
                        "suggested_weights": {"unified": 15},
                    }
                ],
                "reasoning": "Mock pattern discovery response",
            }
        else:
            return {"error": "Unknown prompt type"}

    def _parse_strategy_analysis_response(
        self, response: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """
        Parse ChatGPT response for strategy analysis.

        Args:
            response: Raw ChatGPT response

        Returns:
            Parsed analysis results
        """
        if isinstance(response, dict):
            # Response is already parsed
            result = {
                "analysis_type": "strategy_selection",
                "weight_adjustments": response.get("weight_adjustments", {}),
                "reasoning": response.get("reasoning", "No reasoning provided"),
            }
            return result

        # Try to parse string response as JSON
        try:
            parsed = json.loads(response)
            return {
                "analysis_type": "strategy_selection",
                "weight_adjustments": parsed.get("weight_adjustments", {}),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "error": "Invalid response format - could not parse JSON",
                "analysis_type": "strategy_selection",
                "raw_response": str(response),
            }

    def _parse_modifier_performance_response(
        self, response: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """
        Parse ChatGPT response for modifier performance analysis.

        Args:
            response: Raw ChatGPT response

        Returns:
            Parsed analysis results
        """
        if isinstance(response, dict):
            return {
                "analysis_type": "modifier_performance",
                "modifier_adjustments": response.get("modifier_adjustments", {}),
                "reasoning": response.get("reasoning", "No reasoning provided"),
            }

        try:
            parsed = json.loads(response)
            return {
                "analysis_type": "modifier_performance",
                "modifier_adjustments": parsed.get("modifier_adjustments", {}),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "error": "Invalid response format - could not parse JSON",
                "analysis_type": "modifier_performance",
                "raw_response": str(response),
            }

    def _parse_pattern_discovery_response(
        self, response: Union[Dict[str, Any], str]
    ) -> Dict[str, Any]:
        """
        Parse ChatGPT response for pattern discovery analysis.

        Args:
            response: Raw ChatGPT response

        Returns:
            Parsed analysis results
        """
        if isinstance(response, dict):
            return {
                "analysis_type": "pattern_discovery",
                "suggested_new_modifiers": response.get("suggested_new_modifiers", []),
                "reasoning": response.get("reasoning", "No reasoning provided"),
            }

        try:
            parsed = json.loads(response)
            return {
                "analysis_type": "pattern_discovery",
                "suggested_new_modifiers": parsed.get("suggested_new_modifiers", []),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "error": "Invalid response format - could not parse JSON",
                "analysis_type": "pattern_discovery",
                "raw_response": str(response),
            }
