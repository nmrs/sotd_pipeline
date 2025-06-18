# SOTD Pipeline - Development Workflow Rule
#
# Before considering any task complete or committing changes, you MUST run:
#   make format lint typecheck test
# and ensure all checks pass. This is mandatory for all development and code review workflows.
#
# This rule applies to all phases, features, bugfixes, refactors, and documentation updates.

# SOTD Pipeline - Documentation and Rule Synchronization
#
# Any code, workflow, or process change MUST be reflected in all relevant documentation and
# Cursor rules. Documentation and rules must be updated as part of the same commit(s) as the
# code or process change. This ensures that docs, rules, and code are always in sync for
# reviewers and future contributors.
