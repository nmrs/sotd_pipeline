# Mismatch Identification Tool Requirements

## Objective and Scope

The goal is to create a new tool that improves the identification of potential mismatches in the list of matches. This tool will assist in the manual review process by providing visual indicators and interactive filtering options to quickly identify and correct regex mismatches.

## Existing Tool Reference

The current tool, `analyze_matched.py`, processes matched data files to identify potential mismatches. However, it lacks features for efficient manual review, such as visual indicators and interactive filtering.

## Data to be Processed

The tool will process JSON data files containing match information for products like razors, blades, brushes, and soaps. Each entry includes fields such as:
- `author`: The author of the post.
- `body`: The content of the post.
- `created_utc`: The creation date and time.
- `id`: The unique identifier for the post.
- `thread_id`: The identifier for the thread.
- `thread_title`: The title of the thread.
- `url`: The URL of the post.
- Product-specific fields (`razor`, `blade`, `brush`, `soap`), each containing:
  - `original`: The original text.
  - `matched`: The matched product details.
  - `pattern`: The regex pattern used.
  - `match_type`: The type of match (e.g., exact, brand_fallback).

## Functional Requirements

- Provide visual indicators for potential mismatches.
- Allow interactive filtering of matches to focus on specific products or patterns.
- Highlight products that match multiple regex patterns.

## Non-Functional Requirements

- The tool should be fast and responsive, processing data in under a second for typical use cases.

## Integration Points

- The tool will read existing matched data files but does not need to integrate with other systems or maintain backward compatibility.

## Error Handling

- The tool should fail fast with clear exceptions if it encounters malformed data or other issues.

## Documentation and Support

- A markdown guide will be provided to document the tool's usage and features.

## Version 1.0

This document is ready for handoff to a software architect for implementation design.

## Implementation Plan for Mismatch Identification Tool

### Milestones:

1. **Milestone 1: Design and Prototyping**
   - **Objective**: Finalize the CLI design and prototype the visual indicators and interactive filtering.
   - **Tasks**:
     - Design CLI prompts and options for selecting fields and filtering criteria.
     - Prototype visual indicators similar to those in `analyze_soap_matches.py`.
     - Validate the design with stakeholders.

2. **Milestone 2: Core Functionality Development**
   - **Objective**: Implement the core logic for mismatch identification and interactive filtering.
   - **Tasks**:
     - Develop the data processing module to read and parse JSON data files.
     - Implement the logic for identifying potential mismatches using regex patterns.
     - Develop the interactive filtering module to allow filtering by product and regex matches.

3. **Milestone 3: Performance Optimization**
   - **Objective**: Ensure the tool meets performance requirements.
   - **Tasks**:
     - Optimize data processing to ensure the tool launches in under 5 seconds.
     - Conduct performance testing with various data sizes.

4. **Milestone 4: Error Handling and Documentation**
   - **Objective**: Implement error handling and develop user documentation.
   - **Tasks**:
     - Implement error handling to fail fast with clear exceptions for malformed data.
     - Develop a simple user guide documenting how to launch the tool and available options.

5. **Milestone 5: Testing and Validation**
   - **Objective**: Conduct thorough testing and validate the tool against requirements.
   - **Tasks**:
     - Perform unit and integration testing, including edge cases.
     - Validate the tool's functionality and performance with stakeholders.

### Modules or Components:

1. **Data Processing Module**:
   - **Function**: Reads and parses JSON data files, identifies potential mismatches using regex patterns.
   - **Dependencies**: Uses regex patterns from files like `razors.yaml`.

2. **Visual Indicator Module**:
   - **Function**: Provides visual cues for mismatches in the CLI.
   - **Design**: Based on the approach in `analyze_soap_matches.py`.

3. **Interactive Filtering Module**:
   - **Function**: Allows users to filter matches by product and regex matches.
   - **Interface**: CLI prompts for user interaction.

4. **Error Handling Module**:
   - **Function**: Manages exceptions and error reporting, ensuring clear messaging for malformed data.

5. **Documentation and Support Module**:
   - **Function**: Generates markdown documentation and provides user support guides.

### Key Decisions:

1. **Interface Design**: Use a CLI with visual indicators and interactive filtering.
2. **Technology Stack**: Utilize existing regex patterns and matchers for data processing.
3. **Performance Optimization**: Focus on efficient data parsing and regex matching to meet performance goals.

### Risks or Tradeoffs:

1. **Performance vs. Complexity**: Balancing fast processing with the complexity of interactive features.
2. **User Experience**: Ensuring the CLI is intuitive and easy to use.
3. **Scalability**: Designing the tool to handle larger datasets in the future without significant rework.

### Overlooked Aspects:

- **User Feedback Loop**: Consider incorporating a mechanism for gathering user feedback to improve the tool iteratively.
- **Future Extensibility**: Design the tool with modularity in mind to facilitate future enhancements or integrations.

## Correct Matches Integration (2025-06)

- The match phase must check `data/correct_matches.yaml` for confirmed matches before attempting regex or fallback matching.
- If a match is found in correct_matches.yaml, it is returned with `match_type: exact` and all catalog fields are preserved.
- If not found, regex patterns are used (`match_type: regex`).
- Fallbacks (brand, alias, etc.) are used only if both fail.
- This improves accuracy and allows for manual correction of edge cases.

## Output Structure

```python
{
    "original": "input_string",
    "matched": { ... all catalog fields ... },
    "match_type": "exact|regex|alias|brand|unmatched",
    "pattern": str | None
}
``` 