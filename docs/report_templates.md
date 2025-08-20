# Report Templates

The SOTD Pipeline now supports flexible, customizable templates for both hardware and software reports. This allows users to easily modify the entire report structure and content without changing the code.

## Overview

The template system uses Markdown files with variable replacement and table placeholders to generate complete reports. Templates are stored in `data/report_templates/` as individual `.md` files and can be easily edited by users to customize the entire report structure.

## Template File Structure

The template system uses individual Markdown files in the `data/report_templates/` directory:

```
data/report_templates/
├── hardware.md              # Monthly hardware report template
├── software.md              # Monthly software report template
├── annual_hardware.md       # Annual hardware report template
└── annual_software.md       # Annual software report template
```

Each template file contains the complete report structure with variables and table placeholders. The system automatically loads templates based on the report type being generated.

## Template Content Structure

Each template file contains the complete report content with variable placeholders and table placeholders. Here's an example structure:

```markdown
# Hardware Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

Welcome to your SOTD Hardware Report for {{month_year}}

## Notes & Caveats

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report.

## Razors

{{tables.razors}}

## Blades

{{tables.blades}}
```

**Note**: Each template file contains the complete report structure. The system automatically substitutes variables and table placeholders to generate the final report.

## Available Template Variables

### Monthly Hardware Report Variables

The following variables are available for the monthly hardware report template:

| Variable | Description | Example Output |
|----------|-------------|----------------|
| `{{month_year}}` | Month and year in display format | `January 2025` |
| `{{total_shaves}}` | Total number of shaves (formatted with commas) | `1,234` |
| `{{unique_shavers}}` | Number of unique users | `567` |
| `{{avg_shaves_per_user}}` | Average shaves per user | `2.2` |
| `{{median_shaves_per_user}}` | Median shaves per user | `1.0` |
| `{{unique_razors}}` | Number of unique razors used | `234` |
| `{{unique_blades}}` | Number of unique blades used | `123` |
| `{{unique_brushes}}` | Number of unique brushes used | `89` |

### Monthly Software Report Variables

The following variables are available for the monthly software report template:

| Variable | Description | Example Output |
|----------|-------------|----------------|
| `{{month_year}}` | Month and year in display format | `January 2025` |
| `{{total_shaves}}` | Total number of shaves (formatted with commas) | `1,234` |
| `{{unique_shavers}}` | Number of unique users | `567` |
| `{{avg_shaves_per_user}}` | Average shaves per user | `2.2` |
| `{{median_shaves_per_user}}` | Median shaves per user | `1.0` |
| `{{unique_soaps}}` | Number of unique soaps used | `585` |
| `{{unique_brands}}` | Number of unique soap brands/makers | `136` |
| `{{total_samples}}` | Total number of sample shaves used | `89` |
| `{{sample_percentage}}` | Percentage of shaves that used samples | `7.2%` |
| `{{sample_users}}` | Number of unique users who used samples | `67` |
| `{{sample_brands}}` | Number of unique brands sampled | `23` |

### Annual Report Variables

The following variables are available for annual report templates:

| Variable | Description | Example Output |
|----------|-------------|----------------|
| `{{year}}` | Year in display format | `2025` |
| `{{total_shaves}}` | Total number of shaves (formatted with commas) | `15,678` |
| `{{unique_shavers}}` | Total number of unique users | `1,234` |
| `{{avg_shaves_per_user}}` | Average shaves per user | `12.7` |
| `{{median_shaves_per_user}}` | Median shaves per user | `8.0` |
| `{{included_months}}` | Number of months included in the data | `12` |
| `{{missing_months}}` | Number of months missing from the data | `0` |
| `{{total_samples}}` | Total number of sample shaves used | `1,234` |
| `{{sample_percentage}}` | Percentage of shaves that used samples | `7.9%` |
| `{{sample_users}}` | Number of unique users who used samples | `456` |
| `{{sample_brands}}` | Number of unique brands sampled | `89` |

## Available Table Placeholders

### Hardware Report Tables

The following table placeholders are available for hardware reports:

- `{{tables.razors}}` - Top razors by usage
- `{{tables.blades}}` - Top blades by usage  
- `{{tables.blade-usage-distribution}}` - Blade usage distribution (uses per blade)
- `{{tables.brushes}}` - Top brushes by usage
- `{{tables.soap-makers}}` - Top soap makers by usage
- `{{tables.soaps}}` - Top soaps by usage
- `{{tables.top-sampled-soaps}}` - Top sampled soaps by usage

### Software Report Tables

The following table placeholders are available for the software report template:

| Placeholder | Description | Content |
|-------------|-------------|---------|
| `{{tables.soap-makers}}` | Soap maker statistics | Top soap makers |
| `{{tables.soaps}}` | Soap usage statistics | Top soaps by usage |
| `{{tables.top-sampled-soaps}}` | Sample usage statistics | Top sampled soaps by usage |
| `{{tables.brand-diversity}}` | Brand diversity statistics | Unique scents per brand |
| `{{tables.top-shavers}}` | Top shaver statistics | Users with most shaves |

## How to Customize Templates

1. **Edit the template files**: Open the appropriate template file in `data/report_templates/` in your preferred text editor
2. **Modify content**: Change the text content as needed while preserving the Markdown structure
3. **Use variables**: Include variables where you want dynamic content (e.g., `{{total_shaves}}`)
4. **Add table placeholders**: Insert table placeholders where you want tables (e.g., `{{tables.razors}}`)
5. **Customize structure**: Organize sections, headers, and tables however you prefer
6. **Save changes**: The changes will take effect immediately on the next report generation

## Template Syntax

### Variable Replacement

Variables use double curly braces: `{{variable_name}}`

Example:
```markdown
# Hardware Report - {{month_year}}
- **{{total_shaves}} shaves** were analyzed this month
```

### Table Placeholders

Table placeholders use the format: `{{tables.table-name}}`

Example:
```markdown
## Razor Statistics
{{tables.razors}}
{{tables.razor-manufacturers}}
```

### Markdown Formatting

Templates use standard Markdown syntax:
```markdown
# Main Header
## Section Header
### Subsection Header

* Bullet points
* More bullet points

**Bold text** and *italic text*

[Link text](URL)
```

## Customization Examples

### Minimal Hardware Template
```markdown
# Hardware Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

## Razors
{{tables.razors}}

## Blades
{{tables.blades}}

## Brushes
{{tables.brushes}}
```

### Detailed Hardware Template with Custom Headers
```markdown
# Hardware Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

## Notes & Caveats

This report covers hardware usage for {{total_shaves}} shaves from {{unique_shavers}} users.

## Razor Analysis

### Most Popular Razors
{{tables.razors}}

### Razor Manufacturers
{{tables.razor-manufacturers}}

## Blade Analysis

### Most Popular Blades
{{tables.blades}}

## Brush Analysis

### Most Popular Brushes
{{tables.brushes}}

### Handle Makers
{{tables.brush-handle-makers}}

### Knot Makers
{{tables.brush-knot-makers}}
```

### Software Template Example
```markdown
# Software Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report. Collectively, these shavers used {{unique_soaps}} distinct soaps from {{unique_brands}} distinct brands.

## Soap Makers
{{tables.soap-makers}}

## Soaps
{{tables.soaps}}

## Brand Diversity
{{tables.brand-diversity}}
```

## Testing Templates

The template system includes comprehensive testing to ensure templates work correctly:

### Test Fixtures
- Templates are stored in `tests/fixtures/report_template.yaml` for testing
- Tests use shared fixtures to avoid code duplication
- Both unit and integration tests use the same template structure

### Test Coverage
- **Unit tests**: Test template variable replacement and content generation
- **Integration tests**: Test complete report generation with sample data
- **Template validation**: Ensure templates load correctly and contain required sections

### Running Template Tests
```bash
# Run all report tests
python -m pytest tests/report/ -v

# Run specific template tests
python -m pytest tests/report/test_template_integration.py -v
```

## Error Handling

The system follows a **fast-fail** approach. If the template directory is missing, contains errors, or has missing template files, report generation will fail immediately with a clear error message. This ensures that configuration issues are caught early and explicitly.

**Common errors:**
- `Templates directory not found: data/report_templates` - Template directory is missing
- `Template 'hardware' not found. Available templates: ...` - Template file is missing
- `Unknown table name: invalid-table` - Invalid table placeholder name
- Markdown syntax errors - Invalid Markdown structure

## Adding New Templates

To add new template types:

1. Create a new Markdown file in `data/report_templates/`:
```markdown
# New Report Type - {{month_year}}

**Total Shaves:** {{total_shaves}}

## Content
{{tables.example-table}}
```

2. Update the code to use the new template
3. Add appropriate variables if needed
4. Update this documentation with the new variables

## Best Practices

1. **Backup your templates**: Keep a backup of your custom templates
2. **Test changes**: Generate a test report after making template changes
3. **Use descriptive variable names**: Make variable names clear and meaningful
4. **Maintain formatting**: Preserve the Markdown formatting for proper report rendering
5. **Version control**: Consider adding your custom templates to version control
6. **Organize logically**: Group related tables together with descriptive headers
7. **Keep it readable**: Use clear section headers and logical flow
8. **Use shared templates**: Leverage the testing infrastructure to validate template changes

## Troubleshooting

### Template Not Found
- Check that the template directory exists at `data/report_templates/`
- Verify the template file name matches what the code expects
- Ensure the Markdown syntax is valid

### Table Placeholder Not Working
- Check that the table placeholder name is correct (see available placeholders above)
- Verify the table name uses hyphens, not underscores
- Ensure the table placeholder is properly formatted: `{{tables.table-name}}`

### Report Generation Fails
- This is expected behavior when templates are missing or invalid
- Check the template files for syntax errors
- Verify the template structure matches the expected format
- Look for clear error messages that indicate what's wrong

### Test Failures
- Ensure test templates in `tests/fixtures/report_template.yaml` are up to date
- Check that template changes don't break existing tests
- Verify that both unit and integration tests pass 