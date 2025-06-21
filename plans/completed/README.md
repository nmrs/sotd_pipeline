# Data Recovery Plans

This folder contains plans and documentation for recovering missing or corrupted data in the SOTD pipeline.

## Folder Organization

### Analysis Files
- `missing_months_analysis.mdc` - Comprehensive analysis of missing months (2016-2025)
- `missing_months_recovery_plan.mdc` - Step-by-step recovery plan for missing data

### Future Plans
- Additional recovery plans for specific data issues
- Investigation reports for data quality problems
- Prevention strategies and monitoring setup

## Current Issues

### Missing Months (2024-12-20)
- **11 months completely missing**: Both threads and comments absent
- **7 months missing comments only**: Threads exist but comments don't
- **Pattern**: August and May months consistently affected

### Priority Levels
- **High**: Missing months affecting data analysis accuracy
- **Medium**: Comment-only gaps for future months
- **Low**: Historical data gaps with limited impact

## How to Use These Plans

### 1. Start with Analysis
Review `missing_months_analysis.mdc` to understand the scope and patterns of missing data.

### 2. Follow Recovery Plan
Use `missing_months_recovery_plan.mdc` as a step-by-step guide for data recovery:
- Phase 1: Investigation and root cause analysis
- Phase 2: Data recovery execution
- Phase 3: Validation and quality assurance
- Phase 4: Prevention and monitoring

### 3. Update Status
As tasks are completed, update the plan files with:
- Completion status
- Results and findings
- Lessons learned
- Next steps

## Best Practices

### Before Starting Recovery
1. **Backup existing data** - Ensure current data is safe
2. **Test on small samples** - Verify approach before full recovery
3. **Document everything** - Record all findings and decisions

### During Recovery
1. **Follow the plan** - Stick to the structured approach
2. **Validate frequently** - Check data quality at each step
3. **Update documentation** - Keep plans current with progress

### After Recovery
1. **Verify completeness** - Ensure all missing data is recovered
2. **Test pipeline integration** - Confirm all phases work with recovered data
3. **Update prevention measures** - Implement monitoring to prevent future gaps

## Related Files

- `plans/bugs/` - Bug fixes and technical issues
- `data/threads/` - Thread data files
- `data/comments/` - Comment data files
- `sotd/fetch/` - Fetch phase code

## Contact

For questions about data recovery plans, refer to the main pipeline documentation or create issues in the project repository.

---
*Last Updated: December 2024* 