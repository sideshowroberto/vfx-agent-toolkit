import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { exec } from 'child_process';
import { promisify } from 'util';
import net from 'net';
import path from 'path';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);

// Get the absolute path to the directory of this file
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

// TCP config to connect to foundry_nuke_bridge
const BRIDGE_HOST = '127.0.0.1';
const BRIDGE_PORT = 8765;

// Create an MCP server for Nuke
const server = new McpServer({
  name: "Nuke Bridge",
  version: "1.0.0",
  description: "MCP server for interacting with Nuke"
});

// Helper function to send commands to the foundry_nuke_bridge
async function sendToNuke(command) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    let data = '';
    let timeout;

    client.connect(BRIDGE_PORT, BRIDGE_HOST, () => {
      client.write(JSON.stringify(command));

      // Set a timeout to detect when response is complete
      // Python bridge doesn't close connection, so we detect end of JSON
      timeout = setTimeout(() => {
        if (data.length > 0) {
          try {
            const result = JSON.parse(data);
            resolve({
              content: [{
                type: "text",
                text: JSON.stringify(result, null, 2)
              }]
            });
          } catch (e) {
            resolve({
              content: [{
                type: "text",
                text: `Error parsing response: ${data}`
              }],
              isError: true
            });
          }
          client.destroy();
        }
      }, 500); // 500ms timeout after last data chunk
    });

    client.on('data', (chunk) => {
      data += chunk;

      // Reset timeout on each data chunk
      if (timeout) clearTimeout(timeout);

      // Try to parse as soon as we have what looks like complete JSON
      try {
        const result = JSON.parse(data);
        clearTimeout(timeout);
        resolve({
          content: [{
            type: "text",
            text: JSON.stringify(result, null, 2)
          }]
        });
        client.destroy();
      } catch (e) {
        // Not complete JSON yet, set new timeout
        timeout = setTimeout(() => {
          try {
            const result = JSON.parse(data);
            resolve({
              content: [{
                type: "text",
                text: JSON.stringify(result, null, 2)
              }]
            });
          } catch (e) {
            resolve({
              content: [{
                type: "text",
                text: `Error parsing response: ${data}`
              }],
              isError: true
            });
          }
          client.destroy();
        }, 500);
      }
    });

    client.on('end', () => {
      if (timeout) clearTimeout(timeout);
      if (data.length > 0) {
        try {
          const result = JSON.parse(data);
          resolve({
            content: [{
              type: "text",
              text: JSON.stringify(result, null, 2)
            }]
          });
        } catch (e) {
          resolve({
            content: [{
              type: "text",
              text: `Error parsing response: ${data}`
            }],
            isError: true
          });
        }
      }
      client.destroy();
    });

    client.on('error', (err) => {
      if (timeout) clearTimeout(timeout);
      resolve({
        content: [{
          type: "text",
          text: `Connection error: ${err.message}`
        }],
        isError: true
      });
      client.destroy();
    });
  });
}

// Create Node tool
server.tool(
  "createNode",
  "Creates a node in Nuke",
  {
    nodeType: z.string().describe("Type of node to create (e.g., 'Read', 'Merge2')"),
    name: z.string().optional().describe("Optional name for the node"),
    inputs: z.array(z.string()).optional().describe("Optional array of input node names")
  },
  async ({ nodeType, name, inputs }) => {
    return await sendToNuke({
      type: 'createNode',
      args: { nodeType, name, inputs }
    });
  }
);

// Set Knob Value tool
server.tool(
  "setKnobValue",
  "Sets a knob value on a node",
  {
    nodeName: z.string().describe("Name of the node"),
    knobName: z.string().describe("Name of the knob to set"),
    value: z.union([z.string(), z.coerce.number(), z.boolean(), z.null(), z.array(z.string())])
      .describe("Value to set the knob to (string, number, boolean, null, or array of strings)")
  },
  async ({ nodeName, knobName, value }) => {
    return await sendToNuke({
      type: 'setKnobValue',
      args: { nodeName, knobName, value }
    });
  }
);

// Get Node tool
server.tool(
  "getNode",
  "Gets information about a node",
  {
    nodeName: z.string().describe("Name of the node to get information about")
  },
  async ({ nodeName }) => {
    return await sendToNuke({
      type: 'getNode',
      args: { nodeName }
    });
  }
);

// Execute tool
server.tool(
  "execute",
  "Renders frames using a Write node",
  {
    writeNodeName: z.string().describe("Name of the Write node to render"),
    frameRangeStart: z.coerce.number().describe("Start frame for rendering"),
    frameRangeEnd: z.coerce.number().describe("End frame for rendering")
  },
  async ({ writeNodeName, frameRangeStart, frameRangeEnd }) => {
    return await sendToNuke({
      type: 'execute',
      args: { writeNodeName, frameRangeStart, frameRangeEnd }
    });
  }
);

// Connect Nodes tool
server.tool(
  "connectNodes",
  "Connects nodes in the node graph",
  {
    inputNode: z.string().describe("Name of the input node"),
    outputNode: z.string().describe("Name of the output node"),
    inputIndex: z.coerce.number().optional().describe("Input index for the connection (default is 0)")
  },
  async ({ inputNode, outputNode, inputIndex = 0 }) => {
    return await sendToNuke({
      type: 'connectNodes',
      args: { inputNode, outputNode, inputIndex }
    });
  }
);

// Set Node Position tool
server.tool(
  "setNodePosition",
  "Sets the position of a node in the node graph",
  {
    nodeName: z.string().describe("Name of the node"),
    xPos: z.coerce.number().describe("X position in the node graph"),
    yPos: z.coerce.number().describe("Y position in the node graph")
  },
  async ({ nodeName, xPos, yPos }) => {
    return await sendToNuke({
      type: 'setNodePosition',
      args: { nodeName, xPos, yPos }
    });
  }
);

// Get Node Position tool
server.tool(
  "getNodePosition",
  "Gets the position of a node in the node graph",
  {
    nodeName: z.string().describe("Name of the node")
  },
  async ({ nodeName }) => {
    return await sendToNuke({
      type: 'getNodePosition',
      args: { nodeName }
    });
  }
);

// Create Group tool
server.tool(
  "createGroup",
  "Creates a group node containing the specified nodes",
  {
    name: z.string().optional().describe("Optional name for the group"),
    nodeNames: z.array(z.string()).optional().describe("Array of node names to include in the group")
  },
  async ({ name, nodeNames }) => {
    return await sendToNuke({
      type: 'createGroup',
      args: { name, nodeNames }
    });
  }
);

// Create LiveGroup tool
server.tool(
  "createLiveGroup",
  "Creates a LiveGroup node for collaborative work",
  {
    name: z.string().optional().describe("Optional name for the LiveGroup"),
    nodeNames: z.array(z.string()).optional().describe("Array of node names to include in the LiveGroup"),
    filePath: z.string().optional().describe("Optional file path to save the LiveGroup")
  },
  async ({ name, nodeNames, filePath }) => {
    return await sendToNuke({
      type: 'createLiveGroup',
      args: { name, nodeNames, filePath }
    });
  }
);

// Load Template tool
server.tool(
  "loadTemplate",
  "Loads a Nuke template (Toolset) into the current script",
  {
    templateName: z.string().describe("Name of the template to load"),
    positionX: z.coerce.number().optional().describe("X position in node graph"),
    positionY: z.coerce.number().optional().describe("Y position in node graph")
  },
  async ({ templateName, positionX, positionY }) => {
    const position = (positionX !== undefined || positionY !== undefined)
      ? { x: positionX ?? 0, y: positionY ?? 0 } : undefined;
    return await sendToNuke({
      type: 'loadTemplate',
      args: { templateName, position }
    });
  }
);

// Save Template tool
server.tool(
  "saveTemplate",
  "Saves selected nodes as a template (Toolset)",
  {
    templateName: z.string().describe("Name for the template"),
    nodeNames: z.array(z.string()).describe("Array of node names to include in the template"),
    category: z.string().optional().describe("Optional category for the template")
  },
  async ({ templateName, nodeNames, category }) => {
    return await sendToNuke({
      type: 'saveTemplate',
      args: { templateName, nodeNames, category }
    });
  }
);

// Create Camera Tracker tool
server.tool(
  "createCameraTracker",
  "Creates and sets up a CameraTracker node",
  {
    sourceName: z.string().describe("Name of the source node to track"),
    numberFeatures: z.coerce.number().optional().describe("Number of features to track (default is 200)"),
    featureSize: z.coerce.number().optional().describe("Size of features to track (default is 15)"),
    featureSeparation: z.coerce.number().optional().describe("Minimum separation between features (default is 20)")
  },
  async ({ sourceName, numberFeatures, featureSize, featureSeparation }) => {
    const trackingFeatures = (numberFeatures !== undefined || featureSize !== undefined || featureSeparation !== undefined)
      ? { numberFeatures, featureSize, featureSeparation } : undefined;
    return await sendToNuke({
      type: 'createCameraTracker',
      args: { sourceName, trackingFeatures }
    });
  }
);

// Execute Camera Solve tool
server.tool(
  "solveCameraTrack",
  "Solves a camera track using the specified CameraTracker node",
  {
    cameraTrackerNode: z.string().describe("Name of the CameraTracker node"),
    solveMethod: z.enum(["Match-Moving", "Full", "Refine"]).optional().describe("Solve method (default is 'Match-Moving')")
  },
  async ({ cameraTrackerNode, solveMethod = "Match-Moving" }) => {
    return await sendToNuke({
      type: 'solveCameraTrack',
      args: { cameraTrackerNode, solveMethod }
    });
  }
);

// Create Scene tool
server.tool(
  "createScene",
  "Creates a 3D scene with optional camera and geometry",
  {
    cameraNode: z.string().optional().describe("Optional name of a camera node to include"),
    geometryNodes: z.array(z.string()).optional().describe("Optional array of geometry node names to include")
  },
  async ({ cameraNode, geometryNodes }) => {
    return await sendToNuke({
      type: 'createScene',
      args: { cameraNode, geometryNodes }
    });
  }
);

// Setup Deep Pipeline tool
server.tool(
  "setupDeepPipeline",
  "Sets up a Deep compositing pipeline",
  {
    inputNodes: z.array(z.string()).describe("Array of input node names (Read nodes with Deep data)"),
    mergeOperation: z.enum(["over", "under", "plus", "difference"]).optional().describe("Merge operation (default is 'over')")
  },
  async ({ inputNodes, mergeOperation = "over" }) => {
    return await sendToNuke({
      type: 'setupDeepPipeline',
      args: { inputNodes, mergeOperation }
    });
  }
);

// Batch Process tool
server.tool(
  "batchProcess",
  "Batch processes a directory of files using Nuke",
  {
    inputDirectory: z.string().describe("Directory containing input files"),
    outputDirectory: z.string().describe("Directory for output files"),
    filePattern: z.string().optional().describe("File pattern to match (e.g., '*.exr')"),
    processScript: z.string().optional().describe("Optional path to a Nuke script to process the files")
  },
  async ({ inputDirectory, outputDirectory, filePattern, processScript }) => {
    return await sendToNuke({
      type: 'batchProcess',
      args: { inputDirectory, outputDirectory, filePattern, processScript }
    });
  }
);

// Run Python Script tool
server.tool(
  "runPythonScript",
  "Runs a Python script in Nuke",
  {
    script: z.string().describe("Python script to execute in Nuke"),
    args: z.record(z.string(), z.string()).optional().describe("Optional string key-value arguments to pass to the script")
  },
  async ({ script, args }) => {
    return await sendToNuke({
      type: 'runPythonScript',
      args: { script, args }
    });
  }
);

// Load Nuke Script tool
server.tool(
  "loadScript",
  "Loads a Nuke script file",
  {
    filePath: z.string().describe("Path to the Nuke script file (.nk)")
  },
  async ({ filePath }) => {
    return await sendToNuke({
      type: 'loadScript',
      args: { filePath }
    });
  }
);

// Save Nuke Script tool
server.tool(
  "saveScript",
  "Saves the current Nuke script to a file",
  {
    filePath: z.string().describe("Path to save the Nuke script file (.nk)")
  },
  async ({ filePath }) => {
    return await sendToNuke({
      type: 'saveScript',
      args: { filePath }
    });
  }
);

// Setup CopyCat tool
server.tool(
  "setupCopyCat",
  "Sets up a CopyCat node for machine learning",
  {
    trainingInputNode: z.string().describe("Name of the input node for training data"),
    trainingOutputNode: z.string().describe("Name of the output node for training data"),
    networkType: z.enum(["Basic", "UNet", "Extended"]).optional().describe("Type of neural network (default is 'Basic')")
  },
  async ({ trainingInputNode, trainingOutputNode, networkType = "Basic" }) => {
    return await sendToNuke({
      type: 'setupCopyCat',
      args: { trainingInputNode, trainingOutputNode, networkType }
    });
  }
);

// Train CopyCat Model tool
server.tool(
  "trainCopyCatModel",
  "Trains a CopyCat neural network model",
  {
    copyCatNodeName: z.string().describe("Name of the CopyCat node"),
    epochs: z.coerce.number().optional().describe("Number of training epochs (default is 100)"),
    batchSize: z.coerce.number().optional().describe("Batch size for training (default is 4)")
  },
  async ({ copyCatNodeName, epochs = 100, batchSize = 4 }) => {
    return await sendToNuke({
      type: 'trainCopyCatModel',
      args: { copyCatNodeName, epochs, batchSize }
    });
  }
);

// Setup Basic Comp tool
server.tool(
  "setupBasicComp",
  "Sets up a basic compositing tree with the provided elements",
  {
    plateNode: z.string().describe("Name of the plate node"),
    fgElements: z.array(z.string()).optional().describe("Array of foreground element node names"),
    bgElements: z.array(z.string()).optional().describe("Array of background element node names")
  },
  async ({ plateNode, fgElements, bgElements }) => {
    return await sendToNuke({
      type: 'setupBasicComp',
      args: { plateNode, fgElements, bgElements }
    });
  }
);

// Setup Keyer tool
server.tool(
  "setupKeyer",
  "Sets up a keying pipeline for the input node",
  {
    inputNodeName: z.string().describe("Name of the input node to key"),
    keyerType: z.enum(["IBK", "Primatte", "Keylight", "UltraKeyer"]).optional().describe("Type of keyer to use (default is 'Primatte')"),
    screenColor: z.array(z.coerce.number()).optional().describe("Optional RGB values for the screen color")
  },
  async ({ inputNodeName, keyerType = "Primatte", screenColor }) => {
    return await sendToNuke({
      type: 'setupKeyer',
      args: { inputNodeName, keyerType, screenColor }
    });
  }
);

// Setup Motion Blur tool
server.tool(
  "setupMotionBlur",
  "Sets up motion blur for the input node",
  {
    inputNodeName: z.string().describe("Name of the input node"),
    vectorNodeName: z.string().optional().describe("Optional name of a node containing motion vectors"),
    motionBlurSamples: z.coerce.number().optional().describe("Number of motion blur samples (default is 10)")
  },
  async ({ inputNodeName, vectorNodeName, motionBlurSamples = 10 }) => {
    return await sendToNuke({
      type: 'setupMotionBlur',
      args: { inputNodeName, vectorNodeName, motionBlurSamples }
    });
  }
);

// Set Project Settings tool
server.tool(
  "setProjectSettings",
  "Sets project settings like frame range, resolution and FPS",
  {
    frameFirst: z.coerce.number().optional().describe("First frame of the project"),
    frameLast: z.coerce.number().optional().describe("Last frame of the project"),
    resolutionWidth: z.coerce.number().optional().describe("Width in pixels"),
    resolutionHeight: z.coerce.number().optional().describe("Height in pixels"),
    fps: z.coerce.number().optional().describe("Frames per second")
  },
  async ({ frameFirst, frameLast, resolutionWidth, resolutionHeight, fps }) => {
    const frameRange = (frameFirst !== undefined && frameLast !== undefined)
      ? { first: frameFirst, last: frameLast } : undefined;
    const resolution = (resolutionWidth !== undefined && resolutionHeight !== undefined)
      ? { width: resolutionWidth, height: resolutionHeight } : undefined;
    return await sendToNuke({
      type: 'setProjectSettings',
      args: { frameRange, resolution, fps }
    });
  }
);

// List Nodes tool
server.tool(
  "listNodes",
  "Lists all nodes in the current script, optionally filtered by type",
  {
    filter: z.string().optional().describe("Optional filter to narrow down the list of nodes (e.g., 'Read')")
  },
  async ({ filter }) => {
    return await sendToNuke({
      type: 'listNodes',
      args: { filter }
    });
  }
);

export { server };
