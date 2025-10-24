# 3D Mesh Coordinate Alignment Tool

A user-friendly GUI application for aligning 3D meshes to custom coordinate systems through interactive point selection.

## Features

- **Interactive GUI** - Easy-to-use interface built with Tkinter
- **Multiple Format Support** - Import and export various 3D file formats
- **Visual Point Selection** - Pick alignment points using an interactive 3D viewer
- **Mesh Downsampling** - Optional mesh simplification for large files
- **Format Validation** - Automatic validation of supported file formats
- **Centered Windows** - All windows appear centered on screen
- **Clear Visual Feedback** - Red sphere markers and coordinate displays

## Supported File Formats

### Export Formats (Verified):
- **STL** (.stl) - Standard Tessellation Language (Binary)
- **STL ASCII** (.stl_ascii) - Standard Tessellation Language (Text)
- **PLY** (.ply) - Polygon File Format
- **OBJ** (.obj) - Wavefront OBJ
- **OFF** (.off) - Object File Format
- **GLB** (.glb) - GL Transmission Format (Binary) **[Recommended]**
- **GLTF** (.gltf) - GL Transmission Format (JSON)
- **COLLADA** (.dae) - Collaborative Design Activity

### Import Formats:
All export formats plus 3MF and other formats supported by trimesh

## Installation

### Required Dependencies:
```bash
pip install trimesh pyvista numpy
```

### Optional Dependencies (for better downsampling):
```bash
pip install fast-simplification
```

If `fast-simplification` is not installed, the tool will automatically use a built-in vertex clustering method instead.

## Usage

### GUI Mode (Recommended):
```bash
python open3d_gui.py
```

1. Click **Browse** to select your input 3D mesh file
2. Choose output location and filename
3. Select desired output format from dropdown
4. (Optional) Enable downsampling and adjust ratio
5. Click **Start Alignment Process**
6. Follow the 3-step interactive point selection:
   - **Step 1**: Select origin point (0,0,0)
   - **Step 2**: Select point along positive X-axis
   - **Step 3**: Select point along positive Y-axis

### Command Line Mode:
```bash
python open3dv1.py <input_file> <output_file> [OPTIONS]

Options:
  --format <format>       Specify output format (stl, glb, obj, ply, etc.)
  --downsample <ratio>    Downsample mesh (e.g., 0.5 for 50% faces)

Examples:
  python open3dv1.py input.3mf output.stl
  python open3dv1.py input.obj output.glb --format glb
  python open3dv1.py input.3mf output.obj --downsample 0.3
```

## Interactive 3D Viewer Controls

### Point Selection:
- **Click on mesh** - Select a point (red sphere marker appears)
- **Press 'N' or ENTER** - Confirm selection and move to next step

### Camera Controls:
- **Left mouse button** - Rotate view
- **Middle mouse / Shift+Left** - Pan view
- **Mouse wheel / Right mouse** - Zoom in/out

## UI Improvements

### Version 2.0 Features:
- ✅ Resizable main window (800x650 default)
- ✅ Larger 3D viewer windows (1200x800)
- ✅ Windows centered on screen automatically
- ✅ Non-overlapping text displays in separate zones
- ✅ Press 'N' or ENTER to continue (no need to close window)
- ✅ Red sphere markers at selected points
- ✅ Better lighting and visual feedback
- ✅ Step progress indicators (1 of 3, 2 of 3, etc.)
- ✅ Auto-updating file extensions when format changes
- ✅ Format validation with helpful warnings
- ✅ Fallback downsampling method (no extra dependencies required)

## How It Works

The tool allows you to define a new coordinate system by selecting 3 points:

1. **Origin Point** - Becomes (0, 0, 0) in the new coordinate system
2. **X-Axis Point** - Defines the positive X direction from origin
3. **Y-Axis Point** - Defines the positive Y direction (should be perpendicular to X)

The Z-axis is automatically computed using the right-hand rule. The tool then:
- Translates the mesh so origin is at (0,0,0)
- Rotates the mesh to align with the new axes
- Exports the transformed mesh in your chosen format

## Text Display Zones

The 3D viewer organizes information in non-overlapping zones:
- **Top Center**: Step progress and main instruction
- **Top Right**: Detailed instructions
- **Bottom Left**: Selected point coordinates (monospace)
- **Bottom Center**: Keyboard shortcuts
- **Bottom Right**: Confirmation prompt

## Downsampling

Two methods are available:

1. **Quadric Decimation** (requires `fast-simplification`)
   - Higher quality results
   - Better preservation of mesh features
   - Install with: `pip install fast-simplification`

2. **Vertex Clustering** (built-in, no dependencies)
   - Automatic fallback method
   - Good for most cases
   - No additional installation needed

## Troubleshooting

### "No module named 'fast_simplification'"
This is optional. The tool will automatically use vertex clustering instead. For better quality downsampling, install the optional package:
```bash
pip install fast-simplification
```

### Windows Unicode Errors
All unicode characters have been replaced with ASCII equivalents (e.g., `[SUCCESS]` instead of ✓)

### Format Not Supported Error
Check that your selected output format is in the supported list. The tool will warn you before attempting unsupported formats.

## License

Open source - feel free to use and modify

## Credits

Generated with [Claude Code](https://claude.com/claude-code)
