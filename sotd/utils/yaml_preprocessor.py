"""
YAML Preprocessor for expanding batch patterns and complex configurations.

Supports:
- Range syntax: "1:8,10:15" -> [1,2,3,4,5,6,7,8,10,11,12,13,14,15]
- Batch patterns with {batch} placeholders
- Variations with suffixes and conditional batches
- Multiple knot types and handle materials
- Complex pattern generation
- Nested structure (known_brushes, other_brushes)
"""

from pathlib import Path
from typing import Any, Dict, List

import yaml


class YAMLPreprocessor:
    """Preprocesses YAML files with batch patterns and complex expansions."""

    def __init__(self):
        self.processed_entries = []

    def parse_range(self, range_str: str) -> List[str]:
        """Parse range syntax like '1:8,10:15' into list of strings."""
        if not range_str:
            return []

        result = []
        for part in range_str.split(","):
            part = part.strip()
            if ":" in part:
                start, end = part.split(":")
                start, end = int(start.strip()), int(end.strip())
                result.extend(str(i) for i in range(start, end + 1))
            else:
                result.append(part.strip())

        return result

    def parse_batches(self, batches_data) -> List[str]:
        """Parse batches data which can be string or list format."""
        if isinstance(batches_data, str):
            return self.parse_range(batches_data)
        elif isinstance(batches_data, list):
            result = []
            for item in batches_data:
                if isinstance(item, str):
                    result.extend(self.parse_range(item))
                elif isinstance(item, int):
                    result.append(str(item))
            return result
        else:
            return []

    def expand_batch_patterns(
        self, brand: str, batch_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Expand a batch configuration into individual entries."""
        entries = []

        # Parse valid batches - support both "valid_batches" and "batches"
        batches_key = "valid_batches" if "valid_batches" in batch_config else "batches"
        valid_batches = self.parse_batches(batch_config.get(batches_key, ""))

        # Get base configuration
        knot_types = batch_config.get("knot_types", ["badger"])
        handle_materials = batch_config.get("handle_materials", ["resin"])
        patterns = batch_config.get("patterns", [])
        variations = batch_config.get("variations", [])
        fiber = batch_config.get("fiber", "Badger")
        knot_size_mm = batch_config.get("knot_size_mm")
        model_name_template = batch_config.get("name", "")

        # Generate base entries
        for batch_num in valid_batches:
            for knot_type in knot_types:
                for handle_material in handle_materials:
                    # Create model name by replacing {batch} with actual number
                    model_name = model_name_template.replace("{batch}", batch_num)

                    entry = {
                        "fiber": fiber,
                        "patterns": [p.replace("{batch}", batch_num) for p in patterns],
                    }
                    if knot_size_mm:
                        entry["knot_size_mm"] = knot_size_mm
                    if knot_type != "badger":
                        entry["knot_type"] = knot_type
                    if handle_material != "resin":
                        entry["handle_material"] = handle_material

                    entries.append((model_name, entry))

        # Generate variation entries
        for variation in variations:
            suffix = variation.get("suffix", "")
            var_batches = self.parse_batches(variation.get("valid_batches", ""))
            var_knot_types = variation.get("knot_types", knot_types)
            var_handle_materials = variation.get("handle_materials", handle_materials)

            for batch_num in var_batches:
                for knot_type in var_knot_types:
                    for handle_material in var_handle_materials:
                        # Create model name by replacing {batch} with actual number
                        model_name = model_name_template.replace("{batch}", batch_num) + suffix

                        entry = {
                            "fiber": fiber,
                            "patterns": [
                                p.replace("{batch}", batch_num) + suffix for p in patterns
                            ],
                            "description": variation.get("description", ""),
                        }
                        if knot_size_mm:
                            entry["knot_size_mm"] = knot_size_mm
                        if knot_type != "badger":
                            entry["knot_type"] = knot_type
                        if handle_material != "resin":
                            entry["handle_material"] = handle_material

                        entries.append((model_name, entry))

        return entries

    def process_yaml_file(self, input_path: Path, output_path: Path) -> None:
        """Process a YAML file, expanding batch patterns."""
        with open(input_path, "r") as f:
            data = yaml.safe_load(f)

        # Handle nested structure (known_brushes, other_brushes)
        processed_data = {}

        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                processed_section = {}

                for brand, brand_config in section_data.items():
                    if isinstance(brand_config, dict) and "batch_patterns" in brand_config:
                        # Process batch patterns
                        brand_entries = {}

                        # Expand batch patterns
                        for batch_config in brand_config["batch_patterns"]:
                            batch_entries = self.expand_batch_patterns(brand, batch_config)
                            for model_name, entry in batch_entries:
                                brand_entries[model_name] = entry

                        # Add any non-batch entries
                        for key, value in brand_config.items():
                            if key != "batch_patterns" and isinstance(value, dict):
                                # This is a regular entry, not a batch
                                brand_entries[key] = value

                        # Sort brand entries alphabetically for user ease
                        sorted_brand_entries = dict(sorted(brand_entries.items()))
                        processed_section[brand] = sorted_brand_entries
                    else:
                        # Regular brand structure (no batch patterns)
                        processed_section[brand] = brand_config

                processed_data[section_name] = processed_section
            else:
                # Simple section
                processed_data[section_name] = section_data

        # Write processed data
        with open(output_path, "w") as f:
            yaml.dump(processed_data, f, default_flow_style=False, sort_keys=False)

    def validate_batch_config(self, batch_config: Dict[str, Any]) -> List[str]:
        """Validate a batch configuration and return any errors."""
        errors = []

        required_fields = ["name", "patterns"]
        for field in required_fields:
            if field not in batch_config:
                errors.append(f"Missing required field: {field}")

        # Check for either valid_batches or batches
        if "valid_batches" not in batch_config and "batches" not in batch_config:
            errors.append("Missing required field: valid_batches or batches")

        return errors


def preprocess_catalogs():
    """Preprocess all catalog files."""
    data_dir = Path("data")

    # Process brushes
    brushes_pre = data_dir / "brushes.pre.yaml"
    brushes_output = data_dir / "brushes.post.yaml"  # Test output

    if brushes_pre.exists():
        preprocessor = YAMLPreprocessor()
        preprocessor.process_yaml_file(brushes_pre, brushes_output)
        print(f"Processed {brushes_pre} -> {brushes_output}")

    # Process handles
    handles_pre = data_dir / "handles.pre.yaml"
    handles_output = data_dir / "handles.post.yaml"  # Test output

    if handles_pre.exists():
        preprocessor = YAMLPreprocessor()
        preprocessor.process_yaml_file(handles_pre, handles_output)
        print(f"Processed {handles_pre} -> {handles_output}")

    # Process knots
    knots_pre = data_dir / "knots.pre.yaml"
    knots_output = data_dir / "knots.post.yaml"  # Test output

    if knots_pre.exists():
        preprocessor = YAMLPreprocessor()
        preprocessor.process_yaml_file(knots_pre, knots_output)
        print(f"Processed {knots_pre} -> {knots_output}")


if __name__ == "__main__":
    preprocess_catalogs()
