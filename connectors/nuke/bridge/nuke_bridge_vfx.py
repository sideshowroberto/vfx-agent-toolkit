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
    print("Successfully imported nuke module and nukescripts")
except ImportError as e:
    print(f"Error: Could not import nuke module: {e}", file=sys.stderr)
    print(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}", file=sys.stderr)
    sys.exit(1)

# Advanced VFX functions

def create_camera_tracker(args):
    """Creates and sets up a CameraTracker node"""
    try:
        source_name = args.get('sourceName')
        tracking_features = args.get('trackingFeatures', {})
        
        if not source_name:
            return {"error": "sourceName is required"}
        
        # Get the source node
        source_node = nuke.toNode(source_name)
        if not source_node:
            return {"error": f"Source node '{source_name}' not found"}
        
        # Create CameraTracker node
        camera_tracker = nuke.createNode("CameraTracker")
        
        # Connect the source node
        camera_tracker.setInput(0, source_node)
        
        # Set tracking features parameters if provided
        if tracking_features:
            number_features = tracking_features.get('numberFeatures')
            feature_size = tracking_features.get('featureSize')
            feature_separation = tracking_features.get('featureSeparation')
            
            if number_features is not None:
                k = camera_tracker.knob('keyframe_tracks') or camera_tracker.knob('number_of_features')
                if k: k.setValue(number_features)

            if feature_size is not None:
                k = camera_tracker.knob('detection_size') or camera_tracker.knob('feature_size')
                if k: k.setValue(feature_size)

            if feature_separation is not None:
                k = camera_tracker.knob('detection_spacing') or camera_tracker.knob('feature_separation')
                if k: k.setValue(feature_separation)
        
        return {
            "success": True,
            "cameraTracker": {
                "name": camera_tracker.name(),
                "source": source_name
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def solve_camera_track(args):
    """Solves a camera track using the specified CameraTracker node"""
    try:
        camera_tracker_node = args.get('cameraTrackerNode')
        solve_method = args.get('solveMethod', "Match-Moving")
        
        if not camera_tracker_node:
            return {"error": "cameraTrackerNode is required"}
        
        # Get the CameraTracker node
        camera_tracker = nuke.toNode(camera_tracker_node)
        if not camera_tracker:
            return {"error": f"CameraTracker node '{camera_tracker_node}' not found"}
        
        # Check if it's a CameraTracker node
        if camera_tracker.Class() != "CameraTracker":
            return {"error": f"Node '{camera_tracker_node}' is not a CameraTracker node"}
        
        # Select the node
        nuke.selectAll()
        nuke.invertSelection()
        camera_tracker.setSelected(True)
        
        # Set the solve method
        solve_methods = {
            "Match-Moving": "matchmoving",
            "Full": "fullsolution",
            "Refine": "refine"
        }
        
        # Execute the solve
        method = solve_methods.get(solve_method, "matchmoving")
        
        # Track features then solve via node knobs (Nuke 15 API)
        track_knob = camera_tracker.knob('track_features') or camera_tracker.knob('track')
        if track_knob:
            track_knob.execute()

        solve_knob = camera_tracker.knob('solve') or camera_tracker.knob('autoSolve')
        if solve_knob:
            solve_knob.execute()
        
        # Get status
        error_knob = camera_tracker.knob("solve_error")
        error_value = error_knob.value() if error_knob else "Unknown"
        
        return {
            "success": True,
            "cameraTracker": camera_tracker_node,
            "solveMethod": solve_method,
            "solveError": error_value
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def create_scene(args):
    """Creates a 3D scene with optional camera and geometry"""
    try:
        camera_node = args.get('cameraNode')
        geometry_nodes = args.get('geometryNodes', [])
        
        # Create Scene node
        scene_node = nuke.createNode("Scene")
        
        # Create Camera node if none provided
        if camera_node:
            camera = nuke.toNode(camera_node)
            if not camera:
                return {"error": f"Camera node '{camera_node}' not found"}
        else:
            camera = nuke.createNode("Camera2")
            camera_node = camera.name()
        
        # Connect camera to the scene
        scene_node.setInput(0, camera)
        
        # Connect geometry nodes if provided
        for i, geo_name in enumerate(geometry_nodes):
            geo_node = nuke.toNode(geo_name)
            if geo_node:
                scene_node.setInput(i + 1, geo_node)
            else:
                return {"error": f"Geometry node '{geo_name}' not found"}
        
        # Create ScanlineRender node
        render_node = nuke.createNode("ScanlineRender")
        render_node.setInput(1, scene_node)
        
        return {
            "success": True,
            "scene": {
                "name": scene_node.name(),
                "camera": camera_node,
                "geometry": geometry_nodes,
                "render": render_node.name()
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def setup_deep_pipeline(args):
    """Sets up a Deep compositing pipeline"""
    try:
        input_nodes = args.get('inputNodes', [])
        merge_operation = args.get('mergeOperation', "over")
        
        if not input_nodes:
            return {"error": "inputNodes is required"}
        
        # Check if input nodes exist and are valid
        node_objects = []
        for node_name in input_nodes:
            node = nuke.toNode(node_name)
            if not node:
                return {"error": f"Node '{node_name}' not found"}
            node_objects.append(node)
        
        # Set up the deep pipeline
        created_nodes = []
        deep_nodes = []
        
        # Create DeepRead or DeepFromImage nodes for each input
        for i, node in enumerate(node_objects):
            # Determine if we need DeepFromImage or if it's already a deep node
            if node.Class() == "Read":
                file_path = node.knob('file').value()
                if file_path.lower().endswith('.exr'):
                    # Check if the EXR has deep data
                    try:
                        channels = node.channels()
                        has_deep = any(c.startswith('deep.') for c in channels)
                    except:
                        has_deep = False
                    
                    if has_deep:
                        # It's a deep EXR, use DeepRead
                        deep_node = nuke.createNode("DeepRead")
                        deep_node.knob('file').setValue(file_path)
                    else:
                        # Convert to deep
                        deep_node = nuke.createNode("DeepFromImage")
                        deep_node.setInput(0, node)
                else:
                    # Not an EXR, convert to deep
                    deep_node = nuke.createNode("DeepFromImage")
                    deep_node.setInput(0, node)
            else:
                # For any other node, assume we need to convert to deep
                deep_node = nuke.createNode("DeepFromImage")
                deep_node.setInput(0, node)
            
            created_nodes.append(deep_node.name())
            deep_nodes.append(deep_node)
        
        # Create DeepMerge node to combine them all
        if len(deep_nodes) > 1:
            deep_merge = nuke.createNode("DeepMerge")
            deep_merge.knob('operation').setValue(merge_operation)
            
            for i, node in enumerate(deep_nodes):
                deep_merge.setInput(i, node)
            
            created_nodes.append(deep_merge.name())
            
            # Create DeepToImage node to convert back to 2D
            deep_to_image = nuke.createNode("DeepToImage")
            deep_to_image.setInput(0, deep_merge)
            
            created_nodes.append(deep_to_image.name())
            final_node = deep_to_image
        else:
            # Only one deep node, convert back to 2D
            deep_to_image = nuke.createNode("DeepToImage")
            deep_to_image.setInput(0, deep_nodes[0])
            
            created_nodes.append(deep_to_image.name())
            final_node = deep_to_image
        
        return {
            "success": True,
            "deepPipeline": {
                "inputNodes": input_nodes,
                "createdNodes": created_nodes,
                "finalNode": final_node.name(),
                "operation": merge_operation
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def batch_process(args):
    """Batch processes a directory of files using Nuke"""
    try:
        input_directory = args.get('inputDirectory')
        output_directory = args.get('outputDirectory')
        file_pattern = args.get('filePattern', '*')
        process_script = args.get('processScript')
        
        if not input_directory:
            return {"error": "inputDirectory is required"}
        if not output_directory:
            return {"error": "outputDirectory is required"}
        
        # Check if directories exist
        if not os.path.exists(input_directory):
            return {"error": f"Input directory '{input_directory}' does not exist"}
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Find all files matching the pattern
        search_pattern = os.path.join(input_directory, file_pattern)
        files = glob.glob(search_pattern)
        
        if not files:
            return {"error": f"No files found matching pattern '{search_pattern}'"}
        
        processed_files = []
        
        # Process each file
        for file_path in files:
            file_name = os.path.basename(file_path)
            output_path = os.path.join(output_directory, file_name)
            
            # Create a Read node
            read_node = nuke.createNode("Read")
            read_node.knob('file').setValue(file_path)
            
            # Load process script if provided
            if process_script and os.path.exists(process_script):
                nuke.nodePaste(process_script)
                
                # Connect the last created node to the Read node
                for node in nuke.selectedNodes():
                    if node.Class() != "Read":
                        node.setInput(0, read_node)
                
                # Find a Write node to set the output
                write_nodes = [n for n in nuke.allNodes() if n.Class() == "Write"]
                if write_nodes:
                    write_node = write_nodes[0]
                else:
                    # Create a Write node if none exists
                    write_node = nuke.createNode("Write")
                    last_node = None
                    
                    # Find the last node in the processing chain
                    for node in nuke.allNodes():
                        if node.Class() != "Read" and node.Class() != "Write" and node.dependent() == []:
                            last_node = node
                            break
                    
                    if last_node:
                        write_node.setInput(0, last_node)
                    else:
                        write_node.setInput(0, read_node)
                
                # Set the output path
                write_node.knob('file').setValue(output_path)
                
                # Execute the Write node
                nuke.execute(write_node, int(read_node.knob('first').value()), int(read_node.knob('last').value()))
            else:
                # No process script, just copy the file
                write_node = nuke.createNode("Write")
                write_node.setInput(0, read_node)
                write_node.knob('file').setValue(output_path)
                
                # Execute the Write node
                nuke.execute(write_node, int(read_node.knob('first').value()), int(read_node.knob('last').value()))
            
            processed_files.append({
                "input": file_path,
                "output": output_path
            })
            
            # Clear the script for the next file
            nuke.scriptClear()
        
        return {
            "success": True,
            "batchProcess": {
                "inputDirectory": input_directory,
                "outputDirectory": output_directory,
                "filePattern": file_pattern,
                "processedFiles": processed_files
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def setup_copycat(args):
    """Sets up a CopyCat node for machine learning"""
    try:
        training_input_node = args.get('trainingInputNode')
        training_output_node = args.get('trainingOutputNode')
        network_type = args.get('networkType', "Basic")
        
        if not training_input_node:
            return {"error": "trainingInputNode is required"}
        if not training_output_node:
            return {"error": "trainingOutputNode is required"}
        
        # Get the nodes
        input_node = nuke.toNode(training_input_node)
        output_node = nuke.toNode(training_output_node)
        
        if not input_node:
            return {"error": f"Input node '{training_input_node}' not found"}
        if not output_node:
            return {"error": f"Output node '{training_output_node}' not found"}
        
        # Create CopyCat node
        copycat_node = nuke.createNode("CopyCat")
        
        # Connect input and ground truth
        copycat_node.setInput(0, input_node)
        copycat_node.setInput(1, output_node)
        
        # Set network type
        network_types = {
            "Basic": "basic",
            "UNet": "unet",
            "Extended": "extended"
        }
        net_knob = copycat_node.knob('networkType') or copycat_node.knob('network_type')
        if net_knob:
            net_knob.setValue(network_types.get(network_type, "basic"))
        
        return {
            "success": True,
            "copyCat": {
                "name": copycat_node.name(),
                "inputNode": training_input_node,
                "outputNode": training_output_node,
                "networkType": network_type
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def train_copycat_model(args):
    """Trains a CopyCat neural network model"""
    try:
        copycat_node_name = args.get('copyCatNodeName')
        epochs = args.get('epochs', 100)
        batch_size = args.get('batchSize', 4)
        
        if not copycat_node_name:
            return {"error": "copyCatNodeName is required"}
        
        # Get the CopyCat node
        copycat_node = nuke.toNode(copycat_node_name)
        if not copycat_node:
            return {"error": f"CopyCat node '{copycat_node_name}' not found"}
        
        # Check if it's a CopyCat node
        if copycat_node.Class() != "CopyCat":
            return {"error": f"Node '{copycat_node_name}' is not a CopyCat node"}
        
        # Set training parameters
        k = copycat_node.knob('epochs') or copycat_node.knob('num_epochs')
        if k: k.setValue(epochs)
        k = copycat_node.knob('batchSize') or copycat_node.knob('batch_size')
        if k: k.setValue(batch_size)

        # Start training
        train_knob = copycat_node.knob('train') or copycat_node.knob('startTraining')
        if train_knob:
            train_knob.execute()
        
        # Wait for training to complete (this will block until training is done)
        # In a real implementation, this should be run in a background thread
        # to avoid locking up the bridge
        
        # Get training results
        loss = copycat_node.knob('trainingLoss').value()
        epoch_count = copycat_node.knob('completedEpochs').value()
        
        return {
            "success": True,
            "copyCatTraining": {
                "node": copycat_node_name,
                "completedEpochs": epoch_count,
                "finalLoss": loss
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def setup_basic_comp(args):
    """Sets up a basic compositing tree with the provided elements"""
    try:
        plate_node = args.get('plateNode')
        fg_elements = args.get('fgElements', [])
        bg_elements = args.get('bgElements', [])
        
        if not plate_node:
            return {"error": "plateNode is required"}
        
        # Get the plate node
        plate = nuke.toNode(plate_node)
        if not plate:
            return {"error": f"Plate node '{plate_node}' not found"}
        
        created_nodes = []
        
        # Process background elements
        bg_merge = None
        if bg_elements:
            # Create a merge node for background elements
            bg_merge = nuke.createNode("Merge2")
            bg_merge.knob('operation').setValue('under')
            bg_merge.setInput(0, plate)
            created_nodes.append(bg_merge.name())
            
            last_node = bg_merge
            
            # Connect background elements in sequence
            for i, bg_name in enumerate(bg_elements):
                bg_node = nuke.toNode(bg_name)
                if not bg_node:
                    return {"error": f"Background node '{bg_name}' not found"}
                
                if i == 0:
                    bg_merge.setInput(1, bg_node)
                else:
                    new_merge = nuke.createNode("Merge2")
                    new_merge.knob('operation').setValue('under')
                    new_merge.setInput(0, last_node)
                    new_merge.setInput(1, bg_node)
                    created_nodes.append(new_merge.name())
                    last_node = new_merge
        
        # Process foreground elements
        fg_merge = None
        if fg_elements:
            # Determine what node to use as the base
            base_node = bg_merge if bg_merge else plate
            
            # Create a merge node for foreground elements
            fg_merge = nuke.createNode("Merge2")
            fg_merge.knob('operation').setValue('over')
            fg_merge.setInput(0, base_node)
            created_nodes.append(fg_merge.name())
            
            last_node = fg_merge
            
            # Connect foreground elements in sequence
            for i, fg_name in enumerate(fg_elements):
                fg_node = nuke.toNode(fg_name)
                if not fg_node:
                    return {"error": f"Foreground node '{fg_name}' not found"}
                
                if i == 0:
                    fg_merge.setInput(1, fg_node)
                else:
                    new_merge = nuke.createNode("Merge2")
                    new_merge.knob('operation').setValue('over')
                    new_merge.setInput(0, last_node)
                    new_merge.setInput(1, fg_node)
                    created_nodes.append(new_merge.name())
                    last_node = new_merge
        
        # Determine the final node
        final_node = fg_merge if fg_merge else (bg_merge if bg_merge else plate)
        
        return {
            "success": True,
            "basicComp": {
                "plateNode": plate_node,
                "fgElements": fg_elements,
                "bgElements": bg_elements,
                "createdNodes": created_nodes,
                "finalNode": final_node.name()
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def setup_keyer(args):
    """Sets up a keying pipeline for the input node"""
    try:
        input_node_name = args.get('inputNodeName')
        keyer_type = args.get('keyerType', "Primatte")
        screen_color = args.get('screenColor')
        
        if not input_node_name:
            return {"error": "inputNodeName is required"}
        
        # Get the input node
        input_node = nuke.toNode(input_node_name)
        if not input_node:
            return {"error": f"Input node '{input_node_name}' not found"}
        
        # Create the appropriate keyer node
        keyer_node = None
        
        if keyer_type == "IBK":
            # Create IBK Color and IBK Gizmo nodes
            ibk_color = nuke.createNode("IBKColour")
            ibk_color.setInput(0, input_node)
            
            ibk_gizmo = nuke.createNode("IBKGizmo")
            ibk_gizmo.setInput(0, input_node)
            ibk_gizmo.setInput(1, ibk_color)
            
            keyer_node = ibk_gizmo
            
            if screen_color:
                if len(screen_color) >= 3:
                    ibk_color.knob('screen_type').setValue('pick')
                    ibk_color.knob('red').setValue(screen_color[0])
                    ibk_color.knob('green').setValue(screen_color[1])
                    ibk_color.knob('blue').setValue(screen_color[2])
        
        elif keyer_type == "Primatte":
            keyer_node = nuke.createNode("Primatte")
            keyer_node.setInput(0, input_node)
            
            if screen_color:
                if len(screen_color) >= 3:
                    keyer_node.knob('screenType').setValue(1)  # 1 = Pick
                    keyer_node.knob('screenClrR').setValue(screen_color[0])
                    keyer_node.knob('screenClrG').setValue(screen_color[1])
                    keyer_node.knob('screenClrB').setValue(screen_color[2])
                    
                    # Auto compute screen matte
                    keyer_node.knob('autoComputeScreen').execute()
        
        elif keyer_type == "Keylight":
            keyer_node = nuke.createNode("Keylight")
            keyer_node.setInput(0, input_node)
            
            if screen_color:
                if len(screen_color) >= 3:
                    color_hex = '#{:02x}{:02x}{:02x}'.format(
                        int(screen_color[0] * 255),
                        int(screen_color[1] * 255),
                        int(screen_color[2] * 255)
                    )
                    keyer_node.knob('screenColour').setValue(color_hex)
        
        elif keyer_type == "UltraKeyer":
            keyer_node = nuke.createNode("Ultimatte")
            keyer_node.setInput(0, input_node)
            
            if screen_color:
                if len(screen_color) >= 3:
                    keyer_node.knob('screenColour').setValue([screen_color[0], screen_color[1], screen_color[2], 1.0])
        
        else:
            return {"error": f"Unknown keyer type: {keyer_type}"}
        
        # Create premult node to apply the alpha
        premult = nuke.createNode("Premult")
        premult.setInput(0, keyer_node)
        
        # Create edge blur node to improve edge quality
        edge_blur = nuke.createNode("EdgeBlur")
        edge_blur.setInput(0, premult)
        edge_blur.knob('size').setValue(2)
        
        return {
            "success": True,
            "keyer": {
                "inputNode": input_node_name,
                "keyerType": keyer_type,
                "keyerNode": keyer_node.name(),
                "finalNode": edge_blur.name()
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

def setup_motion_blur(args):
    """Sets up motion blur for the input node"""
    try:
        input_node_name = args.get('inputNodeName')
        vector_node_name = args.get('vectorNodeName')
        motion_blur_samples = args.get('motionBlurSamples', 10)
        
        if not input_node_name:
            return {"error": "inputNodeName is required"}
        
        # Get the input node
        input_node = nuke.toNode(input_node_name)
        if not input_node:
            return {"error": f"Input node '{input_node_name}' not found"}
        
        created_nodes = []
        
        # Set up motion vectors if not provided
        if vector_node_name:
            vector_node = nuke.toNode(vector_node_name)
            if not vector_node:
                return {"error": f"Vector node '{vector_node_name}' not found"}
        else:
            # Create VectorGenerator node
            vector_node = nuke.createNode("VectorGenerator")
            vector_node.setInput(0, input_node)
            vector_node_name = vector_node.name()
            created_nodes.append(vector_node_name)
        
        # Create MotionBlur node
        motion_blur = nuke.createNode("MotionBlur")
        motion_blur.setInput(0, input_node)
        motion_blur.setInput(1, vector_node)
        samples_knob = motion_blur.knob('samples') or motion_blur.knob('mb_samples')
        if samples_knob:
            samples_knob.setValue(motion_blur_samples)
        created_nodes.append(motion_blur.name())
        
        return {
            "success": True,
            "motionBlur": {
                "inputNode": input_node_name,
                "vectorNode": vector_node_name,
                "samples": motion_blur_samples,
                "createdNodes": created_nodes,
                "finalNode": motion_blur.name()
            }
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

# Map commands to functions
vfx_functions = {
    "createCameraTracker": create_camera_tracker,
    "solveCameraTrack": solve_camera_track,
    "createScene": create_scene,
    "setupDeepPipeline": setup_deep_pipeline,
    "batchProcess": batch_process,
    "setupCopyCat": setup_copycat,
    "trainCopyCatModel": train_copycat_model,
    "setupBasicComp": setup_basic_comp,
    "setupKeyer": setup_keyer,
    "setupMotionBlur": setup_motion_blur
}

def main():
    """Main entry point for the VFX bridge script"""
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
    if command in vfx_functions:
        result = vfx_functions[command](args)
    else:
        result = {"error": f"Unknown VFX command: {command}"}
    
    # Print the result as JSON
    print(json.dumps(result))

if __name__ == "__main__":
    main() 