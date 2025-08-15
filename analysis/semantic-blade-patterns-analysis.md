# Semantic Blade Usage Patterns Analysis

## Overview

This document analyzes the 3,007 blade strings that contain **no numbers** to identify semantic usage patterns that are equivalent to numeric usage counts (e.g., "(1)", "(first use)").

## Key Findings

### **High-Volume Semantic Patterns**

#### **1. "(NEW)" / "(new)" Patterns - First-Time Use**
**Volume**: ~80+ strings  
**Semantic Meaning**: Equivalent to "(1)" - first use of a new blade  
**Examples**:
- `Feather Hi-Stainless (NEW)` ✅
- `Gillette Winner Platinum (NEW)` ✅
- `Kai Captain Titan Mild (NEW)` ✅
- `Personna Med Prep (NEW)` ✅
- `Astra (New)` ✅
- `Astra SP (new)` ✅
- `BIC Chrome Platinum (new)` ✅
- `Gillette Nacet (New)` ✅
- `Voskhod(New)` ✅

#### **2. "(fresh)" / "(Fresh)" Patterns - New Blade**
**Volume**: ~30+ strings  
**Semantic Meaning**: Equivalent to "(1)" - fresh, unused blade  
**Examples**:
- `Feather Platinum (fresh)` ✅
- `Astra SP (fresh)` ✅
- `Baili Super Blue (fresh)` ✅
- `Balzano (Fresh)` ✅
- `GSB (fresh)` ✅
- `Voskhod (fresh)` ✅

#### **3. "(new blade)" / "(fresh blade)" Patterns**
**Volume**: ~15+ strings  
**Semantic Meaning**: Explicitly states "new blade" - equivalent to "(1)"  
**Examples**:
- `DOVO Professional (new blade)` ✅
- `Feather Hi-Stainless (new blade)` ✅
- `GSB (fresh blade)` ✅
- `Gillette Platinum Black (fresh blade)` ✅
- `Personna Platinum (new blade)` ✅

#### **4. "(first time)" Patterns**
**Volume**: ~5+ strings  
**Semantic Meaning**: Equivalent to "(1)" - first time using this blade  
**Examples**:
- `Gillette Nacet (first time)` ✅

#### **5. "(Brand new)" Patterns**
**Volume**: ~2+ strings  
**Semantic Meaning**: Equivalent to "(1)" - brand new, unused  
**Examples**:
- `Big Ben, (Brand new)` ✅

### **Medium-Volume Semantic Patterns**

#### **6. "(first use)" / "(First Use)" Patterns**
**Volume**: ~15+ strings  
**Semantic Meaning**: Equivalent to "(1)" - first use of blade  
**Examples**:
- `Astra Superior Platinum Double Edge (first use)` ✅
- `Derby Extra (first use)` ✅
- `Feather (first use)` ✅
- `Gillette Silver Blue (first use)` ✅

#### **7. "(first shave)" / "(First shave)" Patterns**
**Volume**: ~5+ strings  
**Semantic Meaning**: Equivalent to "(1)" - first shave with blade  
**Examples**:
- `Gillette 7 o'clock Super Stainless (first shave)` ✅

### **Low-Volume Semantic Patterns**

#### **8. "(unopened)" / "(sealed)" Patterns**
**Volume**: ~1-2 strings  
**Semantic Meaning**: Equivalent to "(1)" - still sealed/unopened  
**Examples**: Found in some variations

#### **9. "(just opened)" / "(Just opened)" Patterns**
**Volume**: ~1-2 strings  
**Semantic Meaning**: Equivalent to "(1)" - just opened package  
**Examples**: Found in some variations

## Pattern Classification Recommendations

### **Primary Semantic Categories**

#### **Category 1: New/First-Time Use (High Priority)**
- **Patterns**: `(NEW)`, `(new)`, `(fresh)`, `(Fresh)`, `(new blade)`, `(fresh blade)`
- **Volume**: ~125+ strings
- **Impact**: High - clear semantic meaning, high volume
- **Implementation**: Easy regex patterns

#### **Category 2: Explicit Usage Descriptors (Medium Priority)**
- **Patterns**: `(first time)`, `(first use)`, `(first shave)`, `(Brand new)`
- **Volume**: ~25+ strings
- **Impact**: Medium - clear semantic meaning, moderate volume
- **Implementation**: Easy regex patterns

#### **Category 3: Contextual Descriptors (Low Priority)**
- **Patterns**: `(unopened)`, `(sealed)`, `(just opened)`
- **Volume**: ~5+ strings
- **Impact**: Low - clear semantic meaning, low volume
- **Implementation**: Easy regex patterns

## Implementation Strategy

### **Phase 1: High-Impact Patterns**
1. **Add "(NEW)" / "(new)" patterns** to `simple_blade_count` category
2. **Add "(fresh)" / "(Fresh)" patterns** to `simple_blade_count` category
3. **Add "(new blade)" / "(fresh blade)" patterns** to `simple_blade_count` category

### **Phase 2: Medium-Impact Patterns**
1. **Add "(first time)" patterns** to `explicit_usage_count` category
2. **Add "(first use)" / "(first shave)" patterns** to `explicit_usage_count` category
3. **Add "(Brand new)" patterns** to `simple_blade_count` category

### **Phase 3: Low-Impact Patterns**
1. **Add remaining contextual patterns** as needed
2. **Monitor for additional semantic patterns**

## Expected Coverage Impact

### **Current Coverage**:
- **Strings with numbers**: 24,376 (89.0% of unique)
- **Strings without numbers**: 3,007 (11.0% of unique)

### **Projected Coverage After Implementation**:
- **High-impact patterns**: +125 strings → **89.5% coverage**
- **Medium-impact patterns**: +25 strings → **89.6% coverage**
- **Total improvement**: +150 strings → **+0.6% coverage**

### **Coverage Target**:
- **Goal**: 90%+ coverage of all unique blade strings
- **Current**: 89.0% coverage
- **After semantic patterns**: 89.6% coverage
- **Remaining gap**: 0.4% (about 110 strings)

## Conclusion

The semantic pattern analysis reveals **significant opportunities** to improve blade usage pattern coverage:

1. **High-volume patterns** like "(NEW)" and "(fresh)" represent clear first-time usage
2. **Medium-volume patterns** like "(first time)" provide explicit usage context
3. **Implementation is straightforward** with simple regex patterns
4. **Coverage improvement** of +0.6% brings us closer to 90% target

**Recommendation**: Implement Phase 1 (high-impact patterns) immediately, as these represent clear semantic equivalents to numeric usage counts and would significantly improve our understanding of blade usage patterns.

## Next Steps

1. **Implement Phase 1 patterns** in the extraction script
2. **Test coverage improvement** with real data
3. **Evaluate Phase 2 patterns** based on implementation complexity
4. **Monitor for additional semantic patterns** in remaining unanalyzed strings
