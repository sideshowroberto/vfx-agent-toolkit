#!/usr/bin/env python
import os
import socket
import threading
import json
import sys
import traceback

# Import Nuke modules when running inside Nuke
try:
    import nuke
    import nukescripts
    print("Successfully connected to Nuke")
except ImportError:
    print("ERROR: This script must be run from within Nuke's Python environment.")
    sys.exit(1)

# Import our enhanced bridge modules
try:
    # Load functions from our bridge files
    from nuke_bridge_core import (
        create_node, set_knob_value, get_node, execute_render,
        connect_nodes, set_node_position, get_node_position,
        create_group, create_live_group, load_template, save_template,
        list_nodes, run_python_script, load_script, save_script,
        set_project_settings
    )
    
    from nuke_bridge_vfx import (
        create_camera_tracker, solve_camera_track, create_scene,
        setup_deep_pipeline, batch_process, setup_copycat,
        train_copycat_model, setup_basic_comp, setup_keyer,
        setup_motion_blur
    )
    
    print("Successfully imported bridge modules")
except ImportError as e:
    print(f"Error importing bridge modules: {e}")
    # If running directly in Nuke, the modules may not be available
    # Define placeholder functions to avoid errors
    def missing_function(args):
        return {"error": "Function not available. Bridge modules not loaded correctly."}
    
    # Basic functions
    create_node = missing_function
    set_knob_value = missing_function
    get_node = missing_function
    execute_render = missing_function
    connect_nodes = missing_function
    set_node_position = missing_function
    get_node_position = missing_function
    create_group = missing_function
    create_live_group = missing_function
    load_template = missing_function
    save_template = missing_function
    list_nodes = missing_function
    run_python_script = missing_function
    load_script = missing_function
    save_script = missing_function
    set_project_settings = missing_function
    
    # VFX functions
    create_camera_tracker = missing_function
    solve_camera_track = missing_function
    create_scene = missing_function
    setup_deep_pipeline = missing_function
    batch_process = missing_function
    setup_copycat = missing_function
    train_copycat_model = missing_function
    setup_basic_comp = missing_function
    setup_keyer = missing_function
    setup_motion_blur = missing_function

# Map command names to functions
COMMAND_MAP = {
    # Basic commands
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
    "setProjectSettings": set_project_settings,
    
    # VFX commands
    "createCameraTracker": create_camera_tracker,
    "solveCameraTrack": solve_camera_track,
    "createScene": create_scene,
    "setupDeepPipeline": setup_deep_pipeline,
    "batchProcess": batch_process,
    "setupCopyCat": setup_copycat,
    "trainCopyCatModel": train_copycat_model,
    "setupBasicComp": setup_basic_comp,
    "setupKeyer": setup_keyer,
    "setupMotionBlur": setup_motion_blur,
}

class NukeBridgeServer(threading.Thread):
    def __init__(self, host='127.0.0.1', port=8765):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
    
    def run(self):
        self.server.bind((self.host, self.port))
        self.server.listen(1)
        self.running = True
        print(f"[NukeBridgeServer] Server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client, address = self.server.accept()
                print(f"[NukeBridgeServer] Client connected: {address}")
                
                # Handle client in a separate thread
                client_thread = threading.Thread(target=self.handle_client, args=(client,))
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"[NukeBridgeServer] Error accepting connection: {e}")
    
    def handle_client(self, client):
        try:
            while self.running:
                data = client.recv(8192)
                if not data:
                    break
                
                try:
                    # Parse the command
                    print(f"[NukeBridgeServer] Received data: {data.decode('utf-8')}")
                    command = json.loads(data.decode('utf-8'))
                    result = self.process_command(command)
                    print(f"[NukeBridgeServer] Sending response: {json.dumps(result)}")
                    
                    # Send the result back
                    response = json.dumps(result).encode('utf-8')
                    client.sendall(response)
                    
                except json.JSONDecodeError as e:
                    error_response = json.dumps({"error": f"Invalid JSON: {str(e)}"}).encode('utf-8')
                    client.sendall(error_response)
                except Exception as e:
                    traceback.print_exc()
                    error_response = json.dumps({"error": str(e)}).encode('utf-8')
                    client.sendall(error_response)
        
        except Exception as e:
            print(f"[NukeBridgeServer] Client handling error: {e}")
        finally:
            print("[NukeBridgeServer] Client disconnected")
            client.close()
    
    def process_command(self, command):
        print(f"[NukeBridgeServer] Processing command: {command}")
        cmd_type = command.get('type')
        args = command.get('args', {})

        # Execute the command using our function map
        if cmd_type in COMMAND_MAP:
            try:
                print(f"[NukeBridgeServer] Command type '{cmd_type}' found in COMMAND_MAP")
                print(f"[NukeBridgeServer] Function to call: {COMMAND_MAP[cmd_type]}")
                print(f"[NukeBridgeServer] Arguments: {args}")
                print(f"[NukeBridgeServer] About to execute function...")

                func = COMMAND_MAP[cmd_type]
                if nuke.GUI:
                    # GUI mode: executeInMainThread is async and returns None.
                    # Use a threading.Event to capture the actual return value.
                    result_holder = [None]
                    done = threading.Event()

                    def run_in_main(f=func, a=args):
                        result_holder[0] = f(a)
                        done.set()

                    nuke.executeInMainThread(run_in_main)
                    done.wait(timeout=30)
                    result = result_holder[0]
                else:
                    # Non-GUI mode: single-threaded, call directly
                    result = func(args)

                print(f"[NukeBridgeServer] Function execution completed")
                print(f"[NukeBridgeServer] Result type: {type(result)}")
                print(f"[NukeBridgeServer] Result: {result}")
                return result
            except Exception as e:
                print(f"[NukeBridgeServer] EXCEPTION CAUGHT!")
                print(f"[NukeBridgeServer] Exception type: {type(e).__name__}")
                print(f"[NukeBridgeServer] Exception message: {str(e)}")
                traceback.print_exc()
                return {
                    "error": f"Error executing {cmd_type}: {str(e)}",
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                    "code_version": "v2_with_debug"
                }
        else:
            print(f"[NukeBridgeServer] Command type '{cmd_type}' NOT found in COMMAND_MAP")
            return {"error": f"Unknown command type: {cmd_type}"}
    
    def stop(self):
        self.running = False
        try:
            # Connect to ourselves to break the accept() call
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.host, self.port))
            self.server.close()
        except:
            pass

# Global server instance
_nuke_bridge_server = None

def start_nuke_bridge_server():
    global _nuke_bridge_server
    if _nuke_bridge_server is None or not _nuke_bridge_server.running:
        _nuke_bridge_server = NukeBridgeServer()
        _nuke_bridge_server.daemon = True
        _nuke_bridge_server.start()
        
        # Add a menu command to stop the server
        try:
            toolbar = nuke.menu('Nuke')
            m = toolbar.addMenu('NukeBridge')
            m.addCommand('Stop Bridge Server', 'stop_nuke_bridge_server()')
        except:
            pass
        
        return True
    return False

def stop_nuke_bridge_server():
    global _nuke_bridge_server
    if _nuke_bridge_server and _nuke_bridge_server.running:
        _nuke_bridge_server.stop()
        _nuke_bridge_server = None
        return True
    return False

# Auto-start the server when this module is imported
start_nuke_bridge_server()

# Print success message
print("=" * 50)
print("Enhanced Nuke Bridge is now running on port 8765")
print("You can now connect to Nuke via TCP at 127.0.0.1:8765")
print("=" * 50) 