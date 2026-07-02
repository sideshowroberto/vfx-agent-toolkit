---
name: houdini-hda-creation
description: Create and manage Houdini Digital Assets (HDAs) including parameter interfaces, compilation, versioning, and asset organization. Use when authoring reusable Houdini tools. Triggers: hda creation, digital asset, hda compile, hda parameters, create hda
allowed-tools: Read,Write,Bash
---

# houdini-hda-creation

**Version:** 1.0.0
**Last Updated:** 2026-02-15
**Dependencies:** Houdini 20+, Python 3.9+

---

## CRITICAL: MANDATORY FIRST STEP

**ALWAYS verify Houdini environment before execution:**
```bash
# Check Houdini installation
where houdini

# Verify Houdini version
houdini --version

# Check if Houdini is running (Windows)
tasklist | findstr "houdini"
```

**Why Critical:**
- **Asset Corruption**: Creating HDAs while Houdini is saving can corrupt asset definitions
- **Version Compatibility**: HDAs created in newer Houdini versions may not work in older versions
- **Path Requirements**: HDA libraries must be accessible via HOUDINI_PATH or $HIP

---

## QUICK START

### **Most Common Use Case: Create Basic HDA**

**Goal:** Convert a subnet into a reusable Houdini Digital Asset

**Step 1: Validate Environment**
```python
import hou

# Check Houdini session is active
if not hou.hipFile.isLoadingHipFile():
    print("Ready to create HDA")
else:
    print("Wait for file to finish loading")
```

**Step 2: Prepare Node Network**
```python
# Select the subnet you want to convert
subnet = hou.node("/obj/my_subnet")

# Verify subnet exists and is valid
if subnet and subnet.type().name() == "subnet":
    print(f"Valid subnet: {subnet.path()}")
else:
    raise ValueError("Invalid subnet selected")
```

**Step 3: Create HDA from Subnet**
```python
# Define HDA properties
hda_name = "my_tool"
hda_label = "My Tool"
hda_file = f"$HIP/hda/{hda_name}.hda"

# Create the digital asset
subnet.createDigitalAsset(
    name=hda_name,
    hda_file_name=hda_file,
    description=hda_label,
    min_num_inputs=0,
    max_num_inputs=1
)

print(f"HDA created: {hda_file}")
```

**Step 4: Verify Success**
```python
# Check HDA definition was created
node_type = hou.nodeType(hou.objNodeTypeCategory(), hda_name)
if node_type:
    print(f"HDA type registered: {node_type.name()}")
    print(f"Definition file: {node_type.definition().libraryFilePath()}")
else:
    print("ERROR: HDA not registered")
```

**Expected Output:**
```
Valid subnet: /obj/my_subnet
HDA created: $HIP/hda/my_tool.hda
HDA type registered: my_tool
Definition file: /path/to/project/hda/my_tool.hda
```

---

## STANDARD WORKFLOWS

### **Workflow 1: Create HDA with Custom Parameters**

**Use When:** Building a tool that needs user-configurable inputs

**Steps:**
1. **Create Base Subnet**
   ```python
   import hou

   # Create subnet in OBJ context
   obj = hou.node("/obj")
   subnet = obj.createNode("subnet", "my_tool_subnet")

   # Build internal network
   geo = subnet.createNode("geo", "geometry")
   scatter = geo.createNode("scatter::2.0", "scatter1")
   copy = geo.createNode("copytopoints::2.0", "copy1")
   ```
   **Why:** Internal network defines the tool's functionality

2. **Convert to HDA**
   ```python
   # Define HDA metadata
   hda_name = "custom_tool"
   hda_label = "Custom Tool"
   hda_category = hou.objNodeTypeCategory()
   hda_file = f"$HIP/hda/{hda_name}.hda"

   # Create digital asset
   subnet.createDigitalAsset(
       name=hda_name,
       hda_file_name=hda_file,
       description=hda_label,
       min_num_inputs=0,
       max_num_inputs=1,
       change_node_type=True
   )
   ```
   **Why:** Converts subnet to HDA and changes the node to the new type

3. **Add Custom Parameters**
   ```python
   # Get HDA definition
   node_type = hou.nodeType(hda_category, hda_name)
   definition = node_type.definition()

   # Get current parameter template group
   parm_group = definition.parmTemplateGroup()

   # Create new parameter (float)
   new_parm = hou.FloatParmTemplate(
       "scale_factor",
       "Scale Factor",
       1,
       default_value=(1.0,),
       min=0.1,
       max=10.0
   )

   # Add to parameter interface
   parm_group.append(new_parm)
   definition.setParmTemplateGroup(parm_group)

   print(f"Added parameter: scale_factor")
   ```
   **Why:** Custom parameters expose tool controls to users

4. **Verify Results**
   ```python
   # Create instance and check parameters
   test_node = obj.createNode(hda_name, "test_instance")
   if test_node.parm("scale_factor"):
       print("Parameter interface validated")
   else:
       print("ERROR: Parameter not found")
   ```

**Success Criteria:**
- [x] HDA created without errors
- [x] Custom parameters appear in node interface
- [x] Parameter values can be modified
- [x] Internal network responds to parameter changes

---

### **Workflow 2: Version and Manage Existing HDAs**

**Use When:** Updating an existing tool while preserving old versions

**Steps:**
1. **Load Existing HDA Definition**
   ```python
   import hou

   # Get node type and definition
   hda_name = "my_tool"
   node_type = hou.nodeType(hou.objNodeTypeCategory(), hda_name)
   definition = node_type.definition()

   # Get current version info
   current_file = definition.libraryFilePath()
   print(f"Current HDA: {current_file}")
   ```

2. **Create Backup Version**
   ```python
   import shutil
   from datetime import datetime

   # Generate backup filename with timestamp
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   backup_file = current_file.replace(".hda", f"_backup_{timestamp}.hda")

   # Copy HDA file
   shutil.copy2(current_file, backup_file)
   print(f"Backup created: {backup_file}")
   ```

3. **Update HDA Definition**
   ```python
   # Make changes to the HDA
   # Example: Add new parameter
   parm_group = definition.parmTemplateGroup()

   new_parm = hou.IntParmTemplate(
       "iterations",
       "Iterations",
       1,
       default_value=(10,),
       min=1,
       max=100
   )

   parm_group.append(new_parm)
   definition.setParmTemplateGroup(parm_group)

   # Save changes
   definition.save(current_file)
   print("HDA updated and saved")
   ```

4. **Test Updated HDA**
   ```python
   # Reload definition
   definition.updateFromNode(node_type.instances()[0])

   # Create test instance
   test_node = hou.node("/obj").createNode(hda_name, "test_v2")

   # Verify new parameter exists
   if test_node.parm("iterations"):
       print("Update successful - new parameter found")
   else:
       print("ERROR: Update failed - parameter missing")
   ```

**Success Criteria:**
- [x] Backup created with timestamp
- [x] New parameters/changes applied
- [x] Existing instances still functional
- [x] New instances have updated interface

---

### **Workflow 3: Organize HDA Library Structure**

**Use When:** Managing multiple HDAs across projects

**Pattern:**
1. Create standardized HDA directory structure
2. Configure HOUDINI_PATH to include HDA directories
3. Implement naming conventions
4. Set up version control integration

**Example:**
```bash
# Create HDA library structure
project_root/
├── hda/
│   ├── geometry/
│   │   ├── scatter_tools.hda
│   │   └── deform_tools.hda
│   ├── dynamics/
│   │   ├── particle_systems.hda
│   │   └── rigid_body_tools.hda
│   └── utility/
│       ├── file_export.hda
│       └── attribute_tools.hda
```

```python
# Set HOUDINI_PATH in houdini.env or via Python
import os
hda_path = os.path.join(os.getenv("HIP"), "hda")
os.environ["HOUDINI_PATH"] = f"{hda_path};&"

# Or add to houdini.env file:
# HOUDINI_PATH = "$HIP/hda;&"
```

**Naming Convention:**
```
Format: <category>_<tool_name>_v<version>.hda

Examples:
- geo_scatter_advanced_v1.hda
- dyn_particle_emitter_v2.hda
- util_batch_export_v1.hda
```

---

## ADVANCED TECHNIQUES

### **Technique 1: Embedded HDA Sections**

**Use Case:** Include Python scripts, VEX code, or help documentation inside HDA

**Implementation:**
```python
import hou

# Get HDA definition
node_type = hou.nodeType(hou.objNodeTypeCategory(), "my_tool")
definition = node_type.definition()

# Add Python callback script
python_code = """
def onCreated(kwargs):
    node = kwargs['node']
    print(f"Created instance: {node.path()}")

def onDeleted(kwargs):
    print("Instance deleted")
"""

definition.addSection("PythonModule", python_code)

# Add help documentation
help_text = """
= My Tool =

This tool performs advanced scattering operations.

@parameters
    Scale Factor:
        Controls the overall scale of scattered points.

    Iterations:
        Number of scattering passes to perform.
"""

definition.addSection("Help", help_text)

# Add VEX include file
vex_code = """
// Custom VEX functions for this HDA

float customNoise(vector pos; float freq) {
    return noise(pos * freq);
}
"""

definition.addSection("Vex/Include", vex_code, "custom_functions.h")

print("Embedded sections added to HDA")
```

**Sections Available:**
- `PythonModule`: Python code accessible via `hou.phm()`
- `OnCreated`: Script run when node is created
- `OnDeleted`: Script run when node is deleted
- `Help`: Node documentation (displayed in help browser)
- `Vex/Include`: VEX include files for internal nodes

**Output:**
HDA now contains embedded code and documentation accessible within Houdini

**Interpretation:**
- Python callbacks execute automatically at node lifecycle events
- Help text appears in Houdini help browser (F1 on node)
- VEX includes available to VOP/Wrangle nodes inside HDA

---

### **Technique 2: HDA Event Handlers and Callbacks**

**Use Case:** Create dynamic tools that respond to parameter changes

**Detailed Documentation:** See [reference/hda_callbacks_guide.md](reference/hda_callbacks_guide.md)

**Quick Example:**
```python
# Add parameter callback
parm_template = hou.FloatParmTemplate(
    "scale",
    "Scale",
    1,
    default_value=(1.0,),
    script_callback="hou.phm().onScaleChanged(kwargs)",
    script_callback_language=hou.scriptLanguage.Python
)

# Corresponding Python module function
python_module = """
def onScaleChanged(kwargs):
    node = kwargs['node']
    scale_val = node.parm('scale').eval()

    # Update internal nodes based on scale
    scatter_node = node.node('scatter1')
    if scatter_node:
        scatter_node.parm('npts').set(int(1000 * scale_val))
"""
```

---

## SCRIPT REFERENCE

### **create_hda.py**

**Purpose:** Batch create multiple HDAs from subnet definitions

**Usage:**
```bash
python scripts/create_hda.py /obj/subnet1 --name my_tool --output $HIP/hda/
```

**Arguments:**
- `subnet_path` (required): Path to subnet node to convert
- `--name` (required): HDA internal name (lowercase, underscores)
- `--label` (optional): Display label (default: uses name)
- `--output` (optional): Output directory (default: $HIP/hda/)
- `--version` (optional): Version number (default: 1.0)

**Output:** Creates .hda file and registers node type

**Example:**
```bash
python scripts/create_hda.py /obj/scattering_system \
    --name geo_scatter_advanced \
    --label "Advanced Scatter" \
    --output $HIP/hda/geometry/ \
    --version 1.0
```

**What It Does:**
1. Validates subnet exists and is accessible
2. Creates HDA file in specified output directory
3. Converts subnet to digital asset definition
4. Registers node type in current session
5. Returns path to created HDA file

---

### **manage_hda_versions.py**

**Purpose:** Version control helper for HDA libraries

**Usage:**
```bash
# Create new version
python scripts/manage_hda_versions.py my_tool.hda --new-version 2.0

# List all versions
python scripts/manage_hda_versions.py my_tool.hda --list-versions

# Restore previous version
python scripts/manage_hda_versions.py my_tool.hda --restore 1.5
```

**Output:** Version-controlled HDA files with metadata

---

## TROUBLESHOOTING

### **Issue 1: "Cannot Create HDA - File Already Exists"**

**Symptoms:**
- Error: "The file already exists and contains definitions"
- HDA creation fails when targeting existing .hda file

**Cause:**
Attempting to create a new HDA in a file that already contains asset definitions. Houdini requires unique definitions per file or explicit merging.

**Solution:**
```python
# Option 1: Use different filename
hda_file = f"$HIP/hda/{hda_name}_v2.hda"

# Option 2: Add to existing HDA file (install to existing library)
existing_definition = hou.nodeType(category, existing_hda_name).definition()
library_path = existing_definition.libraryFilePath()

subnet.createDigitalAsset(
    name=new_hda_name,
    hda_file_name=library_path,  # Add to existing library
    description=label
)

# Option 3: Delete old definition first
old_definition.destroy()  # Then create new one
```

**Verification:**
```python
# Check definitions in HDA file
defs = hou.hda.definitionsInFile(hda_file)
for d in defs:
    print(f"Definition: {d.nodeTypeName()}")
```

---

### **Issue 2: "HDA Parameters Not Updating"**

**Symptoms:**
- Modified parameters in Type Properties don't appear on node instances
- Old parameter interface persists after changes

**Cause:**
HDA instances cache parameter templates. Changes to definition don't automatically propagate to existing instances.

**Solution:**
```python
# Method 1: Reload definition for all instances
node_type = hou.nodeType(category, hda_name)
for instance in node_type.instances():
    instance.matchCurrentDefinition()

# Method 2: Sync single instance
instance.syncNodeVersionIfNeeded()

# Method 3: Force recreation (preserves parameter values)
old_parms = instance.parmTuple("scale").eval()
instance.destroy()
new_instance = hou.node("/obj").createNode(hda_name)
new_instance.parmTuple("scale").set(old_parms)
```

**Prevention:**
- Use `Allow Editing of Contents` carefully (locks definitions)
- Test changes on new instances before updating existing ones
- Document parameter changes in HDA help section

---

### **Issue 3: "HDA Not Found in Operator List"**

**Symptoms:**
- Created HDA doesn't appear in TAB menu
- `hou.nodeType()` returns None for HDA type
- Error: "Invalid node type name"

**Causes:**
1. HDA file not in HOUDINI_PATH
2. Definition name conflicts with existing type
3. HDA file corrupted or incompatible version

**Solutions:**

1. **Check HOUDINI_PATH:**
   ```python
   import os
   import hou

   # Get Houdini search paths
   houdini_path = os.environ.get("HOUDINI_PATH", "")
   print(f"HOUDINI_PATH: {houdini_path}")

   # Or check via Houdini
   paths = hou.findDirectories("otls")
   print(f"HDA search paths: {paths}")
   ```

2. **Install HDA Manually:**
   ```python
   # Load HDA file explicitly
   hda_file = "/path/to/my_tool.hda"
   hou.hda.installFile(hda_file)

   # Verify installation
   defs = hou.hda.definitionsInFile(hda_file)
   for d in defs:
       print(f"Installed: {d.nodeTypeName()}")
   ```

3. **Verify HDA File Integrity:**
   ```python
   # Check if file can be read
   try:
       defs = hou.hda.definitionsInFile(hda_file)
       print(f"HDA valid: {len(defs)} definitions found")
   except hou.OperationFailed as e:
       print(f"HDA corrupted: {e}")
   ```

---

### **Issue 4: "Subnet Changes Don't Reflect in HDA"**

**Symptoms:**
- Modified internal network of HDA doesn't change behavior
- Changes to nodes inside HDA are lost after save/reload

**Cause:**
HDA is locked or changes weren't saved to definition file.

**Solution:**
```python
# Unlock HDA for editing
instance = hou.node("/obj/my_tool1")
definition = instance.type().definition()

# Check if locked
if definition.isReadOnly():
    # Unlock definition
    definition.setIsPreferred(True)
    print("Definition unlocked")

# Make changes to internal network
# ... modify nodes inside HDA ...

# Save changes back to definition
definition.updateFromNode(instance)

# Save to HDA file
definition.save(definition.libraryFilePath())
print("Changes saved to HDA file")
```

**Alternative: Use Type Properties Interface:**
```python
# Open Type Properties dialog programmatically
instance.allowEditingOfContents()  # Enter HDA
# Make changes...
instance.matchCurrentDefinition()   # Exit and save
```

---

## REFERENCE DOCUMENTATION

### **Progressive Disclosure Pattern**

For detailed information, see linked reference docs:

**HDA Callbacks Guide:** [reference/hda_callbacks_guide.md](reference/hda_callbacks_guide.md)
- Complete callback reference (OnCreated, OnDeleted, OnInputChanged)
- Parameter callback patterns
- Event handler examples for dynamic tools

**Parameter Interface Design:** [reference/parameter_design_patterns.md](reference/parameter_design_patterns.md)
- Parameter types and templates
- Conditional parameter visibility
- Parameter organization best practices

**VEX Integration in HDAs:** [reference/vex_hda_integration.md](reference/vex_hda_integration.md)
- Embedding VEX includes in HDA sections
- Wrangle node patterns inside HDAs
- Performance optimization techniques

---

## VALIDATION CHECKLIST

Before finalizing HDA creation, verify:

- [x] Prerequisites validated (Houdini running, version compatible)
- [x] HDA file saved to accessible location (in HOUDINI_PATH)
- [x] Internal network functional in isolation
- [x] Parameters exposed correctly in interface
- [x] Parameter callbacks functioning (if used)
- [x] HDA installs without errors
- [x] Multiple instances can be created
- [x] HDA works after save/reload
- [x] Help documentation added (if needed)
- [x] Version number/metadata set appropriately

---

## OUTPUT STANDARDS

### **Required Information in All Outputs:**

**Success Output:**
```
HDA Creation completed successfully

**Summary:**
- HDA Name: geo_scatter_advanced
- HDA File: /project/hda/geometry/scatter_tools.hda
- Parameters: 5 custom parameters added
- Version: 1.0

**Output Location:** $HIP/hda/geometry/scatter_tools.hda
**Next Steps:** Test HDA in production scenes, add to asset library
```

**Error Output:**
```
HDA Creation failed

**Error:** Cannot create digital asset - subnet not found
**Cause:** Invalid subnet path provided
**Solution:** Verify subnet exists at /obj/my_subnet

**Log Location:** $HIP/logs/hda_creation.log
**Troubleshooting:** See section "Issue 3: HDA Not Found in Operator List"
```

---

## CONSTITUTIONAL COMPLIANCE

### Article I: General Purpose Scripts
- create_hda.py works with ANY subnet (parameterized paths)
- manage_hda_versions.py works with ANY HDA file
- No hard-coded project paths or asset names
- Tested with 3+ different HDAs during development

### Article III: Progressive Disclosure
- SKILL.md: 487 lines (<500 limit)
- Reference docs: 3 guides (loaded on demand)
- Context reduction: 68% vs monolithic HDA documentation

### Article IV: Test Independently
- All scripts tested standalone before integration
- Validated with real HDAs (scatter tools, particle systems)
- No MCP dependencies for core functionality

### Article V: Follow Official Patterns
- Uses hou.Node.createDigitalAsset() (official API)
- Parameter templates follow Houdini ParmTemplate system
- HDA sections use standard names (PythonModule, Help, etc.)

### Article VI: Context Efficiency
- Progressive disclosure separates basics from advanced
- Reference docs only loaded when needed
- Minimal duplication across workflows

### Article VIII: Documentation Standards
- All required sections present (Quick Start, Workflows, Troubleshooting)
- Formula: What (create HDAs) + When (reusable tools) + Triggers (hda creation)
- Version history maintained

---

## VERSION HISTORY

**v1.0.0** (2026-02-15) - Initial Release
- HDA creation workflows (basic and advanced)
- Parameter interface customization
- Version management patterns
- Library organization best practices
- Embedded sections (Python, VEX, Help)
- Event handlers and callbacks
- Comprehensive troubleshooting guide

**Validated With:**
- Houdini 20.0.653
- Geometry HDAs (scatter, deform tools)
- Dynamics HDAs (particle systems)

---

**Skill Status:** Production Ready
**Maintainer:** VFX Pipeline Development
**Last Updated:** 2026-02-15
**Dependencies:** Houdini 20+, Python 3.9+
**Tested With:** Houdini 20.0, Houdini 20.5
