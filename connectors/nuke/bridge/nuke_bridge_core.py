#!/usr/bin/env python
import sys
import json
import traceback
import os
import re
import glob
import shutil
from datetime import datetime

# The actual Nuke module - this should be imported when run inside Nuke
try:
    import nuke
    import nukescripts
    print("Successfully imported nuke module")
except ImportError as e:
    print(f"Error: Could not import nuke module: {e}", file=sys.stderr)
    print(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}", file=sys.stderr)
    print(f"Script location: {os.path.abspath(__file__)}", file=sys.stderr)
    sys.exit(1)

# Thread-safe node lookup - _find_node() is unreliable from background threads;
# nuke.root().nodes() is proven reliable across all thread/GUI-mode combinations.
def _find_node(name):
    for node in nuke.root().nodes():
        if node.name() == name:
            return node
    return None

# Base functions from the original bridge
def create_node(args):
    """Create a node in Nuke"""
    try:
        node_type = args.get('nodeType')
        name = args.get('name')
        inputs = args.get('inputs', [])
        
        if not node_type:
            return {"error": "nodeType is required"}
        
        # Create the node
        if name:
            node = nuke.createNode(node_type, f"name {name}")
        else:
            node = nuke.createNode(node_type)
        
        # Connect inputs if provided
        for i, input_name in enumerate(inputs):
            input_node = _find_node(input_name)
            if input_node:
                node.setInput(i, input_node)
            else:
                return {"error": f"Input node '{input_name}' not found"}
        
        return {
            "success": True,
            "node": {
                "name": node.name(),
                "type": node_type
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def set_knob_value(args):
    """Set a knob value on a node"""
    try:
        node_name = args.get('nodeName')
        knob_name = args.get('knobName')
        value = args.get('value')
        
        if not node_name:
            return {"error": "nodeName is required"}
        if not knob_name:
            return {"error": "knobName is required"}
        if value is None:
            return {"error": "value is required"}
        
        # Get the node
        node = _find_node(node_name)
        if not node:
            return {"error": f"Node '{node_name}' not found"}
        
        # Set the knob value
        knob = node.knob(knob_name)
        if not knob:
            return {"error": f"Knob '{knob_name}' not found on node '{node_name}'"}
        
        # Handle different value types
        try:
            # Check if this is an array knob
            if hasattr(knob, 'dimensions') and knob.dimensions() > 1:
                # For array knobs like color, position, etc.
                if isinstance(value, list) or isinstance(value, tuple):
                    for i, component in enumerate(value):
                        if i < knob.dimensions():
                            knob.setValue(float(component), i)
                else:
                    # Single value for all dimensions
                    for i in range(knob.dimensions()):
                        knob.setValue(float(value), i)
            elif knob.Class() in ["Enumeration_Knob", "Boolean_Knob"]:
                # Handle enumeration knobs
                if isinstance(value, str):
                    knob.setValue(value)
                else:
                    knob.setValue(int(value))
            else:
                # Standard knobs
                knob.setValue(value)
        except Exception as e:
            return {"error": f"Failed to set value: {str(e)}"}
            
        return {
            "success": True,
            "node": node_name,
            "knob": knob_name,
            "value": value
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def get_node(args):
    """Get information about a node"""
    try:
        node_name = args.get('nodeName')
        
        if not node_name:
            return {"error": "nodeName is required"}
        
        # Get the node
        node = _find_node(node_name)
        if not node:
            return {"error": f"Node '{node_name}' not found"}
        
        # Gather basic information about the node
        knob_dict = {}
        for k in node.knobs():
            knob = node.knob(k)
            if knob.visible():
                try:
                    val = knob.value()
                    # Ensure value is JSON-serializable (e.g. Format objects are not)
                    if not isinstance(val, (bool, int, float, str, list, dict, type(None))):
                        val = str(val)
                    knob_dict[k] = val
                except:
                    knob_dict[k] = str(knob)
        
        return {
            "success": True,
            "node": {
                "name": node.name(),
                "type": node.Class(),
                "knobs": knob_dict
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def execute_render(args):
    """Execute a render using a Write node"""
    try:
        write_node_name = args.get('writeNodeName')
        frame_range_start = args.get('frameRangeStart')
        frame_range_end = args.get('frameRangeEnd')
        
        if not write_node_name:
            return {"error": "writeNodeName is required"}
        if frame_range_start is None:
            return {"error": "frameRangeStart is required"}
        if frame_range_end is None:
            return {"error": "frameRangeEnd is required"}
        
        # Get the Write node
        write_node = _find_node(write_node_name)
        if not write_node:
            return {"error": f"Write node '{write_node_name}' not found"}
        
        # Check if it's a Write node
        if write_node.Class() != "Write":
            return {"error": f"Node '{write_node_name}' is not a Write node"}
        
        # Execute the render
        nuke.execute(write_node_name, int(frame_range_start), int(frame_range_end))
        
        return {
            "success": True,
            "writeNode": write_node_name,
            "frameRange": {
                "start": frame_range_start,
                "end": frame_range_end
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

# New functions for node graph management

def connect_nodes(args):
    """Connect nodes in the node graph"""
    try:
        input_node = args.get('inputNode')
        output_node = args.get('outputNode')
        input_index = args.get('inputIndex', 0)
        
        if not input_node:
            return {"error": "inputNode is required"}
        if not output_node:
            return {"error": "outputNode is required"}
        
        # Get the nodes
        in_node = _find_node(input_node)
        out_node = _find_node(output_node)
        
        if not in_node:
            return {"error": f"Input node '{input_node}' not found"}
        if not out_node:
            return {"error": f"Output node '{output_node}' not found"}
        
        # Connect them
        out_node.setInput(input_index, in_node)
        
        return {
            "success": True,
            "inputNode": input_node,
            "outputNode": output_node,
            "inputIndex": input_index
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def set_node_position(args):
    """Set the position of a node in the node graph"""
    try:
        node_name = args.get('nodeName')
        x_pos = args.get('xPos')
        y_pos = args.get('yPos')
        
        if not node_name:
            return {"error": "nodeName is required"}
        if x_pos is None:
            return {"error": "xPos is required"}
        if y_pos is None:
            return {"error": "yPos is required"}
        
        # Get the node
        node = _find_node(node_name)
        if not node:
            return {"error": f"Node '{node_name}' not found"}
        
        # Set position
        node.setXYpos(int(x_pos), int(y_pos))
        
        return {
            "success": True,
            "node": node_name,
            "position": {
                "x": x_pos,
                "y": y_pos
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def get_node_position(args):
    """Get the position of a node in the node graph"""
    try:
        node_name = args.get('nodeName')
        
        if not node_name:
            return {"error": "nodeName is required"}
        
        # Get the node
        node = _find_node(node_name)
        if not node:
            return {"error": f"Node '{node_name}' not found"}
        
        # Get position
        x_pos = node.xpos()
        y_pos = node.ypos()
        
        return {
            "success": True,
            "node": node_name,
            "position": {
                "x": x_pos,
                "y": y_pos
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def create_group(args):
    """Create a group node containing specified nodes"""
    try:
        name = args.get('name')
        node_names = args.get('nodeNames', [])
        
        # Select the nodes to include in the group
        nuke.selectAll()
        nuke.invertSelection()
        
        for node_name in node_names:
            node = _find_node(node_name)
            if node:
                node.setSelected(True)
            else:
                return {"error": f"Node '{node_name}' not found"}
        
        # Create group from selection
        group_node = nuke.collapseToGroup()
        
        # Set name if provided
        if name:
            group_node.setName(name)
        
        return {
            "success": True,
            "group": {
                "name": group_node.name(),
                "nodes": node_names
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def create_live_group(args):
    """Create a LiveGroup node for collaborative work"""
    try:
        name = args.get('name')
        node_names = args.get('nodeNames', [])
        file_path = args.get('filePath')
        
        # Select the nodes to include in the LiveGroup
        nuke.selectAll()
        nuke.invertSelection()
        
        for node_name in node_names:
            node = _find_node(node_name)
            if node:
                node.setSelected(True)
            else:
                return {"error": f"Node '{node_name}' not found"}
        
        # Create LiveGroup from selection
        live_group_node = nuke.collapseToLiveGroup()
        
        # Set name if provided
        if name:
            live_group_node.setName(name)
        
        # Save the LiveGroup to file if path provided
        if file_path:
            live_group_node.knob('file').setValue(file_path)
            live_group_node.knob('save').execute()
        
        return {
            "success": True,
            "liveGroup": {
                "name": live_group_node.name(),
                "nodes": node_names,
                "filePath": file_path
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def load_template(args):
    """Load a Nuke template (Toolset) into the current script"""
    try:
        template_name = args.get('templateName')
        position = args.get('position', {})
        
        if not template_name:
            return {"error": "templateName is required"}
        
        # Get the toolset paths
        toolset_paths = []
        
        # Add standard Nuke toolset path
        nuke_dir = os.path.dirname(nuke.EXE_PATH)
        toolset_paths.append(os.path.join(nuke_dir, 'ToolSets'))
        
        # Add user's .nuke/ToolSets directory
        home_dir = os.path.expanduser('~')
        user_toolset_dir = os.path.join(home_dir, '.nuke', 'ToolSets')
        if os.path.exists(user_toolset_dir):
            toolset_paths.append(user_toolset_dir)
        
        # Search for the template in all toolset paths
        template_path = None
        for path in toolset_paths:
            possible_path = os.path.join(path, template_name + '.nk')
            if os.path.exists(possible_path):
                template_path = possible_path
                break
        
        if not template_path:
            return {"error": f"Template '{template_name}' not found in ToolSets"}
        
        # Get the position to insert the template
        x_pos = position.get('x', 0)
        y_pos = position.get('y', 0)
        
        # Read nodes from the template file
        nuke.nodePaste(template_path)
        
        # Get the newly created nodes
        new_nodes = [n for n in nuke.selectedNodes()]
        
        # Reposition the template if position is specified
        if x_pos != 0 or y_pos != 0:
            for i, node in enumerate(new_nodes):
                node_x = node.xpos()
                node_y = node.ypos()
                node.setXYpos(node_x + x_pos, node_y + y_pos)
        
        return {
            "success": True,
            "template": template_name,
            "nodes": [n.name() for n in new_nodes]
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def save_template(args):
    """Save selected nodes as a template (Toolset)"""
    try:
        template_name = args.get('templateName')
        node_names = args.get('nodeNames', [])
        category = args.get('category', '')
        
        if not template_name:
            return {"error": "templateName is required"}
        if not node_names:
            return {"error": "nodeNames is required"}
        
        # Select the nodes to include in the template
        nuke.selectAll()
        nuke.invertSelection()
        
        for node_name in node_names:
            node = _find_node(node_name)
            if node:
                node.setSelected(True)
            else:
                return {"error": f"Node '{node_name}' not found"}
        
        # Get the user's .nuke/ToolSets directory
        home_dir = os.path.expanduser('~')
        user_toolset_dir = os.path.join(home_dir, '.nuke', 'ToolSets')
        
        # Create the directory if it doesn't exist
        if not os.path.exists(user_toolset_dir):
            os.makedirs(user_toolset_dir)
        
        # Create category directory if specified
        if category:
            category_dir = os.path.join(user_toolset_dir, category)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir)
            save_path = os.path.join(category_dir, template_name + '.nk')
        else:
            save_path = os.path.join(user_toolset_dir, template_name + '.nk')
        
        # Save the selected nodes as a toolset
        nuke.nodeCopy(save_path)
        
        return {
            "success": True,
            "template": {
                "name": template_name,
                "category": category,
                "path": save_path,
                "nodes": node_names
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def list_nodes(args):
    """List all nodes in the current script, optionally filtered by type"""
    try:
        filter_type = args.get('filter', '')
        
        nodes = []
        root_nodes = nuke.root().nodes()
        for node in root_nodes:
            if filter_type and node.Class() != filter_type:
                continue
            # Get basic info for each node
            node_info = {
                "name": node.name(),
                "type": node.Class(),
                "position": {
                    "x": node.xpos(),
                    "y": node.ypos()
                }
            }
            nodes.append(node_info)
        
        return {
            "success": True,
            "count": len(nodes),
            "nodes": nodes
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def run_python_script(args):
    """Run a Python script in Nuke"""
    try:
        script = args.get('script')
        script_args = args.get('args', {})
        
        if not script:
            return {"error": "script is required"}
        
        # Create a namespace for the script
        script_namespace = {'args': script_args, 'nuke': nuke, 'nukescripts': nukescripts}
        
        # Execute the script
        exec(script, script_namespace)
        
        # Get any result the script might have set
        result = script_namespace.get('result', None)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def load_script(args):
    """Load a Nuke script file"""
    try:
        file_path = args.get('filePath')
        
        if not file_path:
            return {"error": "filePath is required"}
        
        if not os.path.exists(file_path):
            return {"error": f"Script file '{file_path}' does not exist"}
        
        # Load the script
        nuke.scriptClear()
        nuke.scriptOpen(file_path)
        
        return {
            "success": True,
            "script": file_path
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def save_script(args):
    """Save the current Nuke script to a file"""
    try:
        file_path = args.get('filePath')
        
        if not file_path:
            return {"error": "filePath is required"}
        
        # Make sure the directory exists
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # Save the script
        nuke.scriptSaveAs(file_path)
        
        return {
            "success": True,
            "script": file_path
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def set_project_settings(args):
    """Set project settings like frame range, resolution and FPS"""
    try:
        frame_range = args.get('frameRange', {})
        resolution = args.get('resolution', {})
        fps = args.get('fps')
        
        root = nuke.root()
        
        # Set frame range if provided
        if frame_range:
            first_frame = frame_range.get('first')
            last_frame = frame_range.get('last')
            
            if first_frame is not None:
                root.knob('first_frame').setValue(first_frame)
            if last_frame is not None:
                root.knob('last_frame').setValue(last_frame)
        
        # Set resolution if provided
        if resolution:
            width = resolution.get('width')
            height = resolution.get('height')
            
            if width is not None and height is not None:
                root.knob('format').setValue(f"{width} {height} 0 0 {width} {height} 1")
        
        # Set FPS if provided
        if fps is not None:
            root.knob('fps').setValue(fps)
        
        return {
            "success": True,
            "settings": {
                "frameRange": {
                    "first": root.knob('first_frame').value(),
                    "last": root.knob('last_frame').value()
                },
                "resolution": {
                    "width": root.width(),
                    "height": root.height()
                },
                "fps": root.knob('fps').value()
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def main():
    """Main entry point for the bridge script"""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified"}))
        return
    
    command = sys.argv[1]
    
    # Parse arguments
    args = {}
    if len(sys.argv) > 2:
        try:
            args = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON arguments"}))
            return
    
    # Execute the appropriate command
    commands = {
        "createNode": create_node,
        "setKnobValue": set_knob_value,
        "getNode": get_node,
        "execute": execute_render,
        "connectNodes": connect_nodes,
        "setNodePosition": set_node_position,
        "getNodePosition": get_node_position,
        "createGroup": create_group,
        "createLiveGroup": create_live_group,
        "loadTemplate": load_template,
        "saveTemplate": save_template,
        "listNodes": list_nodes,
        "runPythonScript": run_python_script,
        "loadScript": load_script,
        "saveScript": save_script,
        "setProjectSettings": set_project_settings
    }
    
    if command in commands:
        result = commands[command](args)
    else:
        result = {"error": f"Unknown command: {command}"}
    
    # Print the result as JSON
    print(json.dumps(result))

if __name__ == "__main__":
    main() 