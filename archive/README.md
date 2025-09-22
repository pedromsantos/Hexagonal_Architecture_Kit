# Archived Language-Specific Rulesets

This directory contains the original language-specific ruleset files that have been superseded by the unified ruleset approach.

## Files Archived

- `ruleset_python.md` - Original Python-specific ruleset
- `ruleset_typescript.md` - TypeScript-specific ruleset
- `ruleset_java.md` - Java-specific ruleset
- `ruleset_csharp.md` - C#-specific ruleset
- `ruleset_rust.md` - Rust-specific ruleset
- `ruleset_go.md` - Go-specific ruleset

## Why Archived?

These files contained significant duplication as they repeated the same architectural rules and explanations across different languages, with only the code examples varying. This approach had several drawbacks:

- **Maintenance Burden**: Changes to rules required updating 6 separate files
- **Consistency Risk**: Easy to miss updates in some files, leading to inconsistencies
- **User Experience**: Users had to choose and stick to one language file, missing cross-language insights

## New Approach

The archived files have been replaced with:

1. **`ruleset_unified.md`** - Single comprehensive ruleset with multi-language code examples
2. **`reference_implementations_guide.md`** - Guide for complete project implementations per language

This new structure provides:

- ✅ Single maintenance point for rules and explanations
- ✅ All language examples visible side-by-side for comparison
- ✅ Reduced duplication while maintaining language-specific guidance
- ✅ Clear separation between quick reference (unified) and complete examples (reference implementations)

## Migration Note

If you were referencing any of these archived files, please update your references to use `ruleset_unified.md` instead. The unified file contains all the same information with improved organization and multi-language support.