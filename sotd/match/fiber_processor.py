import re


class FiberProcessor:
    """Handles processing of fiber information from brush text input."""

    def process_fiber_info(self, value: str, match_dict: dict) -> None:
        """Process fiber information from the input value and update match dictionary."""
        user_fiber = None
        fiber_patterns = {
            "Boar": r"boar",
            "Badger": r"badger",
            "Synthetic": r"synthetic|syn|nylon|plissoft|tuxedo|cashmere",
        }
        for fiber, pat in fiber_patterns.items():
            if re.search(pat, value, re.IGNORECASE):
                user_fiber = fiber
                break

        if user_fiber:
            if match_dict.get("fiber") and match_dict["fiber"].lower() == user_fiber.lower():
                match_dict["fiber_strategy"] = "user_input"
            elif match_dict.get("fiber") and match_dict["fiber"].lower() != user_fiber.lower():
                match_dict["fiber_conflict"] = user_fiber
                match_dict["fiber_strategy"] = "yaml"
            else:
                match_dict["fiber"] = user_fiber
                match_dict["fiber_strategy"] = "user_input"
        else:
            if match_dict.get("fiber_strategy") is None:
                match_dict["fiber_strategy"] = "default" if "default" in value.lower() else "yaml"

    def resolve_fiber(self, updated: dict, parsed_fiber: str | None) -> None:
        """Resolve fiber information in the match result."""
        if "fiber_strategy" not in updated:
            fiber = updated.get("fiber")
            default_fiber = updated.get("default fiber")
            if fiber:
                updated["fiber_strategy"] = "yaml"
                if parsed_fiber and parsed_fiber.lower() != fiber.lower():
                    updated["fiber_conflict"] = f"user_input: {parsed_fiber}"
            elif parsed_fiber:
                updated["fiber"] = parsed_fiber
                updated["fiber_strategy"] = "user_input"
            elif default_fiber:
                updated["fiber"] = default_fiber
                updated["fiber_strategy"] = "default"
            else:
                updated["fiber_strategy"] = "unset"

    def find_fiber_word_indices(
        self, words: list[str], fiber_start: int, fiber_end: int
    ) -> list[int]:
        """Find indices of words that contain fiber information."""
        fiber_indices = []
        for i, word in enumerate(words):
            if fiber_start <= i <= fiber_end:
                fiber_indices.append(i)
        return fiber_indices
