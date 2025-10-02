# Blade Pattern Analysis Report
========================================

## Summary
- Total patterns: 16
- Problematic patterns: 1
- Correct patterns: 15

## Problematic Patterns
These patterns incorrectly match usage count fields:

### Pattern 16
```regex
^\bblade\b\s+(.+)$
```

**Matches problematic cases:**
- `Blade Uses: 1` → `Uses: 1`
- `Blade Count: 5` → `Count: 5`
- `Blade Times: 3` → `Times: 3`
- `Blade Number: 2` → `Number: 2`

**Also matches correct cases:**
- `Blade - Persona Comfort Coat` → `- Persona Comfort Coat`
- `Blade Persona Comfort Coat` → `Persona Comfort Coat`
- `Blade (1)` → `(1)`
- `Blade 1` → `1`
- `Blade - 1` → `- 1`

## All Patterns Analysis
### Pattern 1 ✅ OK
```regex
^✓\s*\bblade\b\s*[-:]\s*(.+)$
```
### Pattern 2 ✅ OK
```regex
^✓\s*\bblade\b\s*[-:]\s*(.+)$
```
### Pattern 3 ✅ OK
```regex
^\*\s*\*\*\bblade\b\*\*\s*[-:]\s*(.+)$
```
### Pattern 4 ✅ OK
```regex
^\*\s*\*\*\bblade\b\*\*\s*(.+)$
```
### Pattern 5 ✅ OK
```regex
^(?:[-*]\s*)?\*\*\bblade\b\*\*\s*[-:]?\s*(.+)$
```
### Pattern 6 ✅ OK
```regex
^(?:[-*]\s*)?\*\*\bblade\b\s*[-:]?\*\*\s*(.+)$
```
### Pattern 7 ✅ OK
```regex
^(?:[-*]\s*)?\*\*\bblade\b\s*[-:]\s*(.+)\*\*$
```
### Pattern 8 ✅ OK
```regex
^(?:[-*•‣⁃▪‧·~+]*\s*)?\bblade\b\s*[-:]\s*(.+)$
```
**Correct matches:**
- `Blade: Persona Comfort Coat` → `Persona Comfort Coat`
- `Blade - Persona Comfort Coat` → `Persona Comfort Coat`
- `Blade: 1` → `1`
- `Blade - 1` → `1`

### Pattern 9 ✅ OK
```regex
^(?:[-*•‣⁃▪‧·~+]*\s*)?\bblade\b\s+[-:]\s*(.+)$
```
**Correct matches:**
- `Blade - Persona Comfort Coat` → `Persona Comfort Coat`
- `Blade - 1` → `1`

### Pattern 10 ✅ OK
```regex
^[^\w\s]?\s*\*\bblade\b\*\s*[-:]\s*(.+)$
```
### Pattern 11 ✅ OK
```regex
^(?:[-*•‣⁃▪‧·~+]\s*)?\#\#\bblade\b\#\#\s*[-:]\s*(.+)$
```
### Pattern 12 ✅ OK
```regex
^(?:[-*]\s*)?__\bblade\b:\__\s*(.+)$
```
### Pattern 13 ✅ OK
```regex
^(?:[-*]\s*)?\*\*\bblade\b\s*//\*\*\s*(.+)$
```
### Pattern 14 ✅ OK
```regex
^[^\w\s]\s*\*+\s*\bblade\b[-:]\s*\*+\s*(.*)$
```
### Pattern 15 ✅ OK
```regex
^[^\w\s]\s*\*+\s*\bblade\b\s*\*+[-:]\s*(.*)$
```
### Pattern 16 ❌ PROBLEMATIC
```regex
^\bblade\b\s+(.+)$
```
**Problematic matches:**
- `Blade Uses: 1` → `Uses: 1`
- `Blade Count: 5` → `Count: 5`
- `Blade Times: 3` → `Times: 3`
- `Blade Number: 2` → `Number: 2`

**Correct matches:**
- `Blade - Persona Comfort Coat` → `- Persona Comfort Coat`
- `Blade Persona Comfort Coat` → `Persona Comfort Coat`
- `Blade (1)` → `(1)`
- `Blade 1` → `1`
- `Blade - 1` → `- 1`
