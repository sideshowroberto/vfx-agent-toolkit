# VFX Documentation: Agent Usage Examples

## Working with documentation-specialist-v2

### Agent Capabilities

The enhanced documentation agent (`.claude/agents/documentation-specialist-v2.md`) implements index-driven updates:

**Index-First Workflow:**
1. [OK] Reads `DEVELOPMENT_DOCUMENTATION_INDEX.md` first
2. [OK] Understands documentation structure
3. [OK] Identifies related files
4. [OK] Maintains cross-references
5. [OK] Updates index after changes

**Update Categories:**
- Session documentation updates
- Feature documentation updates
- Progress tracking updates
- Consistency checks

### Invoking the Agent

**Document a session:**
```
User: "Document today's session on ImagePlate automation"
Agent:
  1. Reads DEVELOPMENT_DOCUMENTATION_INDEX.md
  2. Creates Session_2025-10-25_ImagePlate.md
  3. Updates development guides
  4. Updates index with new session
  5. Synchronizes timestamps
```

**Update feature docs:**
```
User: "Document new foreground plate capability"
Agent:
  1. Reads index to find related guides
  2. Updates DEVELOPMENT_GUIDE.md
  3. Updates QUICK_REFERENCE.md
  4. Updates CAPABILITIES.md
  5. Updates index "Last Updated"
```

**Check consistency:**
```
User: "Check documentation consistency"
Agent:
  1. Reads index completely
  2. Validates all file references
  3. Checks timestamp synchronization
  4. Tests cross-reference links
  5. Reports inconsistencies
```
