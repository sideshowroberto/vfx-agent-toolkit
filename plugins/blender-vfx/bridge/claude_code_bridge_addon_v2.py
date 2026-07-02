"""
Claude Code Bridge Addon for Blender V2.0
==========================================
Enhanced HTTP API server addon for Blender that uses MCP-style main thread execution
to prevent crashes and enable stable screenshot functionality.

Key Improvements:
- Main thread execution using bpy.app.timers (like MCP)
- Stable screenshot functionality using screenshot_area
- Proper context overrides for viewport operations
- Thread-safe result handling

Installation:
1. Open Blender
2. Edit > Preferences > Add-ons
3. Click "Install..." and select this file
4. Enable "Interface: Claude Code Bridge V2"
5. In 3D View, press N to show sidebar
6. Find "Claude Code" tab and click "Start Server"
"""

bl_info = {
    "name": "Claude Code Bridge V2",
    "author": "Blender AI Compatibility Project",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Claude Code",
    "description": "Enhanced HTTP API bridge for Claude Code with MCP-style main thread execution",
    "category": "Interface",
}

import bpy
import threading
import json
import traceback
import sys
import time
import tempfile
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
from contextlib import redirect_stdout
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global server instance
server_instance = None
server_thread = None
SERVER_PORT = 8089

class ResultContainer:
    """Thread-safe container for passing results between threads"""
    def __init__(self):
        self.result = None
        self.ready = False
        self.error = None

class BlenderAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler with MCP-style main thread execution"""
    
    def log_message(self, format, *args):
        """Override to use Blender's console for logging"""
        message = format % args
        print(f"[HTTP] {message}")
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def execute_in_main_thread(self, command):
        """Execute command in Blender's main thread using timer scheduling"""
        result_container = ResultContainer()
        
        def execute_wrapper():
            try:
                # Execute the command in main thread context
                result_container.result = self._execute_command_internal(command)
                result_container.ready = True
            except Exception as e:
                result_container.error = str(e)
                result_container.ready = True
                logger.error(f"Main thread execution error: {str(e)}")
                traceback.print_exc()
            return None  # Don't repeat timer
        
        # Schedule execution in main thread
        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
        
        # Wait for result with timeout
        timeout = 30.0  # 30 second timeout
        start_time = time.time()
        while not result_container.ready and (time.time() - start_time) < timeout:
            time.sleep(0.01)  # Small sleep to prevent busy waiting
        
        if not result_container.ready:
            return {"error": "Operation timed out", "timeout": timeout}
        
        if result_container.error:
            return {"error": result_container.error}
        
        return result_container.result
    
    def _execute_command_internal(self, command):
        """Internal command execution in main thread context"""
        cmd_type = command.get("type")
        params = command.get("params", {})
        
        if cmd_type == "get_scene_info":
            return self.get_scene_info()
        elif cmd_type == "get_version":
            return self.get_version()
        elif cmd_type == "execute_code":
            return self.execute_code(params.get("code", ""))
        elif cmd_type == "clear_scene":
            return self.clear_scene()
        elif cmd_type == "test_compatibility":
            return self.test_compatibility(params.get("api", ""))
        elif cmd_type == "viewport_screenshot":
            return self.viewport_screenshot(params)
        elif cmd_type == "render_preview":
            return self.render_preview(params)
        elif cmd_type == "render_f12_style":
            return self.render_f12_style(params)
        elif cmd_type == "render_full":
            return self.render_full(params)
        else:
            return {"error": f"Unknown command type: {cmd_type}"}
    
    def get_scene_info(self):
        """Get information about the current scene"""
        scene_info = {
            "objects": [],
            "total_objects": len(bpy.data.objects),
            "total_meshes": len(bpy.data.meshes),
            "total_materials": len(bpy.data.materials),
            "render_engine": bpy.context.scene.render.engine
        }
        
        for obj in bpy.data.objects[:10]:  # Limit to first 10 objects
            obj_info = {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "visible": obj.visible_get()
            }
            if obj.type == 'MESH':
                obj_info["vertices"] = len(obj.data.vertices)
                obj_info["polygons"] = len(obj.data.polygons)
            scene_info["objects"].append(obj_info)
        
        return {"status": "success", "result": scene_info}
    
    def get_version(self):
        """Get Blender version information"""
        version_info = {
            "version": bpy.app.version_string,
            "version_cycle": bpy.app.version_cycle,
            "version_major": bpy.app.version[0],
            "version_minor": bpy.app.version[1],
            "version_patch": bpy.app.version[2] if len(bpy.app.version) > 2 else 0,
            "build_date": bpy.app.build_date.decode() if hasattr(bpy.app, 'build_date') else "unknown",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        return {"status": "success", "result": version_info}
    
    def execute_code(self, code):
        """Execute Python code in Blender context"""
        if not code:
            return {"error": "No code provided"}
        
        output = io.StringIO()
        result = None
        error = None
        
        try:
            with redirect_stdout(output):
                exec(code, {'bpy': bpy})
            result = output.getvalue()
        except Exception as e:
            error = str(e)
            traceback.print_exc()
        
        if error:
            return {"success": False, "error": error}
        else:
            return {"success": True, "output": result}
    
    def clear_scene(self):
        """Clear the scene of all objects"""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Clean up orphaned data
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        
        for material in bpy.data.materials:
            if material.users == 0:
                bpy.data.materials.remove(material)
        
        return {"success": True, "message": "Scene cleared"}
    
    def viewport_screenshot(self, params):
        """Take a screenshot of the 3D viewport using MCP method"""
        try:
            # Get parameters
            output_dir = params.get('output_dir', tempfile.gettempdir())
            filename = params.get('filename', 'viewport_capture.png')
            filepath = os.path.join(output_dir, filename)
            max_size = params.get('max_size', 800)
            
            # Find the active 3D viewport (MCP method)
            area = None
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    area = a
                    break
            
            if not area:
                return {"error": "No 3D viewport found"}
            
            # Take screenshot with proper context override (MCP method)
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.screenshot_area(filepath=filepath)
            
            # Optional: Load and resize if needed
            if max_size and max_size > 0:
                try:
                    img = bpy.data.images.load(filepath)
                    width, height = img.size
                    
                    if max(width, height) > max_size:
                        scale = max_size / max(width, height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        img.scale(new_width, new_height)
                        img.file_format = 'PNG'
                        img.save()
                    
                    # Cleanup Blender image data
                    bpy.data.images.remove(img)
                except Exception as e:
                    logger.warning(f"Could not resize image: {e}")
            
            return {
                "success": True,
                "filepath": filepath,
                "message": f"Viewport screenshot saved to {filepath}"
            }
        
        except Exception as e:
            return {"success": False, "error": f"Screenshot failed: {str(e)}"}
    
    def render_preview(self, params):
        """Quick preview render"""
        try:
            # Get parameters
            output_dir = params.get('output_dir', tempfile.gettempdir())
            filename = params.get('filename', 'render_preview.png')
            filepath = os.path.join(output_dir, filename)
            
            # Store original render settings
            original_filepath = bpy.context.scene.render.filepath
            original_resolution_x = bpy.context.scene.render.resolution_x
            original_resolution_y = bpy.context.scene.render.resolution_y
            
            # Set preview render settings
            bpy.context.scene.render.filepath = filepath
            bpy.context.scene.render.resolution_x = 640
            bpy.context.scene.render.resolution_y = 480
            
            # Render
            bpy.ops.render.render(write_still=True)
            
            # Restore original settings
            bpy.context.scene.render.filepath = original_filepath
            bpy.context.scene.render.resolution_x = original_resolution_x
            bpy.context.scene.render.resolution_y = original_resolution_y
            
            return {
                "success": True,
                "filepath": filepath,
                "message": f"Preview render saved to {filepath}",
                "render_engine": bpy.context.scene.render.engine
            }
        
        except Exception as e:
            return {"success": False, "error": f"Render failed: {str(e)}"}
    
    def render_f12_style(self, params):
        """Trigger F12-style render (INVOKE_DEFAULT) and optionally show in Image Editor"""
        try:
            show_in_ui = params.get('show_in_ui', False)
            change_area = params.get('change_area_to_image_editor', False)
            
            # Trigger F12-style render
            result = bpy.ops.render.render('INVOKE_DEFAULT')
            
            # Optionally change a 3D view to Image Editor to show result
            if change_area:
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == 'VIEW_3D':
                            area.type = 'IMAGE_EDITOR'
                            # Set to show render result
                            for space in area.spaces:
                                if space.type == 'IMAGE_EDITOR':
                                    render_result = bpy.data.images.get('Render Result')
                                    if render_result:
                                        space.image = render_result
                                    break
                            break
                    break
            
            # Get render result info
            render_result = bpy.data.images.get('Render Result')
            if render_result:
                size = render_result.size[:]  # Convert to list for JSON
                result_info = {
                    "size": list(size),
                    "has_pixels": len(render_result.pixels) > 0
                }
            else:
                result_info = {"size": [0, 0], "has_pixels": False}
            
            return {
                "success": True,
                "message": "F12-style render triggered",
                "render_result": result_info,
                "operator_result": str(result),
                "area_changed": change_area,
                "render_engine": bpy.context.scene.render.engine
            }
        
        except Exception as e:
            return {"success": False, "error": f"F12 render failed: {str(e)}"}
    
    def render_full(self, params):
        """Full resolution render"""
        try:
            # Get parameters
            output_dir = params.get('output_dir', tempfile.gettempdir())
            filename = params.get('filename', 'render_full.png')
            filepath = os.path.join(output_dir, filename)
            
            # Store original render filepath
            original_filepath = bpy.context.scene.render.filepath
            
            # Set render filepath
            bpy.context.scene.render.filepath = filepath
            
            # Render at full resolution
            bpy.ops.render.render(write_still=True)
            
            # Restore original filepath
            bpy.context.scene.render.filepath = original_filepath
            
            return {
                "success": True,
                "filepath": filepath,
                "message": f"Full render saved to {filepath}",
                "render_engine": bpy.context.scene.render.engine,
                "resolution": f"{bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}"
            }
        
        except Exception as e:
            return {"success": False, "error": f"Render failed: {str(e)}"}
    
    def test_compatibility(self, api_name):
        """Test API compatibility"""
        test_results = {}
        
        # Test EEVEE compatibility
        if api_name == 'EEVEE' or api_name == '':
            try:
                bpy.context.scene.render.engine = 'BLENDER_EEVEE'
                test_results['BLENDER_EEVEE'] = "Works (pre-4.5)"
            except:
                test_results['BLENDER_EEVEE'] = "Not available"
            
            try:
                bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
                test_results['BLENDER_EEVEE_NEXT'] = "Works (4.5.0+)"
            except:
                test_results['BLENDER_EEVEE_NEXT'] = "Not available"
        
        # Test Geometry Nodes compatibility
        if api_name == 'GEOMETRY_NODES' or api_name == '':
            try:
                # Create test object
                bpy.ops.mesh.primitive_cube_add()
                obj = bpy.context.active_object
                
                # Try old API
                try:
                    modifier = obj.modifiers.new(name="TestGeoNodes", type='GEOMETRY_NODES')
                    test_results['GEOMETRY_NODES'] = "Works (pre-4.5)"
                except:
                    test_results['GEOMETRY_NODES'] = "Not available"
                
                # Try new API
                try:
                    modifier = obj.modifiers.new(name="TestNodes", type='NODES')
                    test_results['NODES'] = "Works (4.5.0+)"
                except:
                    test_results['NODES'] = "Not available"
                
                # Clean up test object
                bpy.ops.object.delete()
            except Exception as e:
                test_results['geometry_nodes_error'] = str(e)
        
        return {"status": "success", "result": test_results}
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/health':
                response = {
                    "status": "healthy",
                    "blender_connected": True,
                    "version": bpy.app.version_string
                }
                self.send_json_response(response)
            
            elif path == '/scene':
                result = self.execute_in_main_thread({"type": "get_scene_info"})
                self.send_json_response(result)
            
            elif path == '/version':
                result = self.execute_in_main_thread({"type": "get_version"})
                self.send_json_response(result)
            
            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            logger.error(f"GET error: {str(e)}")
            self.send_json_response({"error": str(e)}, 500)
    
    def do_POST(self):
        """Handle POST requests with main thread execution"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return
        
        try:
            # Map HTTP endpoints to command types
            if path == '/execute':
                command = {"type": "execute_code", "params": {"code": data.get('code', '')}}
            elif path == '/clear':
                command = {"type": "clear_scene"}
            elif path == '/test/compatibility':
                command = {"type": "test_compatibility", "params": {"api": data.get('api', '')}}
            elif path == '/viewport/screenshot':
                command = {"type": "viewport_screenshot", "params": data}
            elif path == '/render/preview':
                command = {"type": "render_preview", "params": data}
            elif path == '/render/f12':
                command = {"type": "render_f12_style", "params": data}
            elif path == '/render/full':
                command = {"type": "render_full", "params": data}
            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)
                return
            
            # Execute in main thread
            result = self.execute_in_main_thread(command)
            self.send_json_response(result)
                
        except Exception as e:
            logger.error(f"POST error: {str(e)}")
            self.send_json_response({"error": str(e)}, 500)


class BLENDER_OT_start_server(bpy.types.Operator):
    """Start the Claude Code HTTP server"""
    bl_idname = "blender.start_claude_server"
    bl_label = "Start Server"
    bl_description = "Start the HTTP server for Claude Code communication"
    
    def execute(self, context):
        global server_instance, server_thread
        
        if server_instance is not None:
            self.report({'INFO'}, "Server already running")
            return {'FINISHED'}
        
        try:
            server_instance = HTTPServer(("localhost", SERVER_PORT), BlenderAPIHandler)
            server_thread = threading.Thread(target=server_instance.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            self.report({'INFO'}, f"Server started on http://localhost:{SERVER_PORT}")
            print(f"Claude Code Bridge V2 started on http://localhost:{SERVER_PORT}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to start server: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BLENDER_OT_stop_server(bpy.types.Operator):
    """Stop the Claude Code HTTP server"""
    bl_idname = "blender.stop_claude_server"
    bl_label = "Stop Server"
    bl_description = "Stop the HTTP server"
    
    def execute(self, context):
        global server_instance, server_thread
        
        if server_instance is None:
            self.report({'INFO'}, "Server not running")
            return {'FINISHED'}
        
        try:
            server_instance.shutdown()
            server_instance.server_close()
            server_instance = None
            
            if server_thread:
                server_thread.join(timeout=2.0)
                server_thread = None
            
            self.report({'INFO'}, "Server stopped")
            print("Claude Code Bridge V2 stopped")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error stopping server: {str(e)}")
        
        return {'FINISHED'}


class BLENDER_PT_claude_code_panel(bpy.types.Panel):
    """Panel for Claude Code Bridge controls"""
    bl_label = "Claude Code Bridge V2"
    bl_idname = "BLENDER_PT_claude_code_v2"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Claude Code"
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="HTTP Bridge Server:")
        
        row = layout.row()
        row.operator("blender.start_claude_server", text="Start Server")
        row.operator("blender.stop_claude_server", text="Stop Server")
        
        layout.separator()
        
        layout.label(text="Status:")
        if server_instance:
            layout.label(text="✅ Server Running", icon='CHECKMARK')
            layout.label(text=f"Port: {SERVER_PORT}")
        else:
            layout.label(text="❌ Server Stopped", icon='X')
        
        layout.separator()
        
        layout.label(text="Features:")
        layout.label(text="• Main thread execution")
        layout.label(text="• Stable screenshots")
        layout.label(text="• Visual renders")
        layout.label(text="• API compatibility testing")


def register():
    bpy.utils.register_class(BLENDER_OT_start_server)
    bpy.utils.register_class(BLENDER_OT_stop_server)
    bpy.utils.register_class(BLENDER_PT_claude_code_panel)


def unregister():
    global server_instance, server_thread
    
    # Stop server on unregister
    if server_instance:
        try:
            server_instance.shutdown()
            server_instance.server_close()
        except:
            pass
        server_instance = None
    
    if server_thread:
        try:
            server_thread.join(timeout=2.0)
        except:
            pass
        server_thread = None
    
    bpy.utils.unregister_class(BLENDER_OT_start_server)
    bpy.utils.unregister_class(BLENDER_OT_stop_server)
    bpy.utils.unregister_class(BLENDER_PT_claude_code_panel)


if __name__ == "__main__":
    register()