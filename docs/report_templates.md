# Report Templates

The SOTD Pipeline now supports flexible, customizable templates for both hardware and software reports. This allows users to easily modify the entire report structure and content without changing the code.

## Overview

The template system uses YAML files with variable replacement and table placeholders to generate complete reports. Templates are stored in `data/report_templates.yaml` and can be easily edited by users to customize the entire report structure.

## Template File Structure

The template file follows this simple structure:

```yaml
hardware:
  template: |
    ## Notes & Caveats
    
    ### Data Collection
    - **{{total_shaves}} shaves** from **{{unique_shavers}} unique users**
    - Users averaged **{{avg_shaves_per_user}} shaves** each
    
    ## Tables
    
    ### Razor Statistics
    {{tables.razor-formats}}
    {{tables.razors}}
    {{tables.razor-manufacturers}}

software:
  template: |
    ## Notes & Caveats
    
    - This data is collected from the r/wetshaving community
    
    ## Tables
    
    ### Soap Statistics
    {{tables.soap-makers}}
    {{tables.soaps}}
    {{tables.brand-diversity}}
```

**Note**: Each report type has a single `template` section containing the complete report structure. This simplified approach makes templates easier to edit and maintain.

## Available Template Variables

### Hardware Report Variables

The following variables are available for the hardware report template:

| Variable | Description | Example Output |
|----------|-------------|----------------|
| `{{total_shaves}}` | Total number of shaves (formatted with commas) | `1,234` |
| `{{unique_shavers}}` | Number of unique users | `567` |
| `{{avg_shaves_per_user}}` | Average shaves per user (formatted to 1 decimal place) | `2.2` |

### Software Report Variables

Currently, the software report template doesn't use any variables, but the system is extensible for future needs.

| Variable | Description | Example Output |
|----------|-------------|----------------|
| *(none currently)* | *(none currently)* | *(none currently)* |

## Available Table Placeholders

### Hardware Report Tables

The following table placeholders are available for the hardware report template:

| Placeholder | Description | Content |
|-------------|-------------|---------|
| `{{tables.razors}}` | Razor usage statistics | Top razors by usage |
| `{{tables.razor-manufacturers}}` | Razor manufacturer statistics | Top manufacturers |
| `{{tables.razor-formats}}` | Razor format statistics | DE, GEM, Injector, etc. |
| `{{tables.blades}}` | Blade usage statistics | Top blades by usage |
| `{{tables.blade-manufacturers}}` | Blade manufacturer statistics | Top blade manufacturers |
| `{{tables.brushes}}` | Brush usage statistics | Top brushes by usage |
| `{{tables.brush-handle-makers}}` | Brush handle maker statistics | Top handle makers |
| `{{tables.brush-knot-makers}}` | Brush knot maker statistics | Top knot makers |
| `{{tables.knot-fibers}}` | Knot fiber type statistics | Badger, Boar, Synthetic |
| `{{tables.knot-sizes}}` | Knot size statistics | Size distribution |
| `{{tables.blackbird-plates}}` | Blackbird plate statistics | Plate usage |
| `{{tables.christopher-bradley-plates}}` | Christopher Bradley plate statistics | Plate usage |
| `{{tables.game-changer-plates}}` | Game Changer plate statistics | Plate usage |
| `{{tables.super-speed-tips}}` | Super Speed tip statistics | Tip color usage |
| `{{tables.straight-widths}}` | Straight razor width statistics | Width distribution |
| `{{tables.straight-grinds}}` | Straight razor grind statistics | Grind types |
| `{{tables.straight-points}}` | Straight razor point statistics | Point types |
| `{{tables.razor-blade-combinations}}` | Razor/blade combination statistics | Most used combinations |
| `{{tables.highest-use-count-per-blade}}` | Highest use count per blade | Per-user blade usage |
| `{{tables.top-shavers}}` | Top shaver statistics | Users with most shaves |

### Software Report Tables

The following table placeholders are available for the software report template:

| Placeholder | Description | Content |
|-------------|-------------|---------|
| `{{tables.soap-makers}}` | Soap maker statistics | Top soap makers |
| `{{tables.soaps}}` | Soap usage statistics | Top soaps by usage |
| `{{tables.brand-diversity}}` | Brand diversity statistics | Unique scents per brand |
| `{{tables.top-shavers}}` | Top shaver statistics | Users with most shaves |

## How to Customize Templates

1. **Edit the template file**: Open `data/report_templates.yaml` in your preferred text editor
2. **Modify content**: Change the text content as needed while preserving the YAML structure
3. **Use variables**: Include variables where you want dynamic content (e.g., `{{total_shaves}}`)
4. **Add table placeholders**: Insert table placeholders where you want tables (e.g., `{{tables.razors}}`)
5. **Customize structure**: Organize sections, headers, and tables however you prefer
6. **Save changes**: The changes will take effect immediately on the next report generation

## Template Syntax

### Variable Replacement

Variables use double curly braces: `{{variable_name}}`

Example:
```yaml
hardware:
  template: |
    - **{{total_shaves}} shaves** were analyzed this month
```

### Table Placeholders

Table placeholders use the format: `{{tables.table-name}}`

Example:
```yaml
hardware:
  template: |
    ## Razor Statistics
    {{tables.razors}}
    {{tables.razor-manufacturers}}
```

### YAML Block Scalar

Use the `|` character for multi-line content:
```yaml
hardware:
  template: |
    ## Notes & Caveats
    
    This is a multi-line
    template content that
    preserves line breaks.
    
    ## Tables
    
    {{tables.razors}}
```

## Customization Examples

### Minimal Template
```yaml
hardware:
  template: |
    ## Hardware Report
    
    {{tables.razors}}
    {{tables.blades}}
    {{tables.brushes}}
```

### Detailed Template with Custom Headers
```yaml
hardware:
  template: |
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
    
    ## User Statistics
    
    ### Top Contributors
    {{tables.top-shavers}}
```

### Reordered Tables
```yaml
hardware:
  template: |
    ## Hardware Report
    
    ## User Statistics
    {{tables.top-shavers}}
    
    ## Razor Statistics
    {{tables.razors}}
    {{tables.razor-manufacturers}}
    
    ## Blade Statistics
    {{tables.blades}}
    
    ## Brush Statistics
    {{tables.brushes}}
```

## Testing Templates

The template system includes comprehensive testing to ensure templates work correctly:

### Test Fixtures
- Templates are stored in `tests/fixtures/report_template.yaml`
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

The system follows a **fast-fail** approach. If the template file is missing, contains errors, or has missing sections, report generation will fail immediately with a clear error message. This ensures that configuration issues are caught early and explicitly.

**Common errors:**
- `Template 'hardware' not found in data/report_templates.yaml` - Template section is missing
- `Section 'template' not found in template 'hardware'` - Template subsection is missing
- `Unknown table name: invalid-table` - Invalid table placeholder name
- YAML syntax errors - Invalid YAML structure

## Adding New Templates

To add new template sections:

1. Add a new section to the YAML file:
```yaml
hardware:
  template: |
    # existing content
new_report_type:
  template: |
    # new template content
```

2. Update the code to use the new template section
3. Add appropriate variables if needed
4. Update this documentation with the new variables

## Best Practices

1. **Backup your templates**: Keep a backup of your custom templates
2. **Test changes**: Generate a test report after making template changes
3. **Use descriptive variable names**: Make variable names clear and meaningful
4. **Maintain formatting**: Preserve the markdown formatting for proper report rendering
5. **Version control**: Consider adding your custom templates to version control
6. **Organize logically**: Group related tables together with descriptive headers
7. **Keep it readable**: Use clear section headers and logical flow
8. **Use shared templates**: Leverage the testing infrastructure to validate template changes

## Troubleshooting

### Template Not Found
- Check that the template file exists at `data/report_templates.yaml`
- Verify the template section name matches what the code expects
- Ensure the YAML syntax is valid

### Table Placeholder Not Working
- Check that the table placeholder name is correct (see available placeholders above)
- Verify the table name uses hyphens, not underscores
- Ensure the table placeholder is properly formatted: `{{tables.table-name}}`

### Report Generation Fails
- This is expected behavior when templates are missing or invalid
- Check the template file for syntax errors
- Verify the template structure matches the expected format
- Look for clear error messages that indicate what's wrong

### Test Failures
- Ensure test templates in `tests/fixtures/report_template.yaml` are up to date
- Check that template changes don't break existing tests
- Verify that both unit and integration tests pass 