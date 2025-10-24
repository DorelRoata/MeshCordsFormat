import trimesh
import pyvista as pv
import numpy as np
import sys

def pick_points(geom, prompt, instruction_text=None):
    print("\n" + "="*70)
    print(prompt)
    if instruction_text:
        print(instruction_text)
    print("="*70)
    print("CONTROLS:")
    print("  - Click on the mesh to select a point")
    print("  - Press 'p' to confirm your selection")
    print("  - Press 'q' to close the window")
    print("="*70 + "\n")

    plotter = pv.Plotter()
    if isinstance(geom, trimesh.Trimesh):
        # Convert trimesh faces to pyvista format
        faces = np.column_stack([np.full(len(geom.faces), 3), geom.faces]).flatten()
        mesh = pv.PolyData(np.asarray(geom.vertices), faces=faces)
    else:
        mesh = pv.PolyData(np.asarray(geom.vertices))

    plotter.add_mesh(mesh, color='lightblue', opacity=0.8)

    # Add text instructions to the 3D window
    if instruction_text:
        plotter.add_text(instruction_text, position='upper_left', font_size=10, color='black')

    # Add coordinate axes for reference
    plotter.add_axes(interactive=True)

    # Callback to display picked point coordinates
    selected_point = {'point': None}
    text_actor = None

    def callback(picked_point):
        nonlocal text_actor
        selected_point['point'] = picked_point
        coord_text = f"Selected Point:\nX: {picked_point[0]:.3f}\nY: {picked_point[1]:.3f}\nZ: {picked_point[2]:.3f}"

        # Remove old text if exists
        if text_actor is not None:
            plotter.remove_actor(text_actor)

        # Add new text with coordinates
        text_actor = plotter.add_text(coord_text, position='lower_left', font_size=12, color='red')
        print(f"Point selected: X={picked_point[0]:.3f}, Y={picked_point[1]:.3f}, Z={picked_point[2]:.3f}")

    plotter.enable_point_picking(callback=callback, show_message=True, color='red', point_size=20)
    plotter.show()

    if plotter.picked_point is None or len(plotter.picked_point) == 0:
        raise ValueError("No point selected.")

    print(f"Final selection: X={plotter.picked_point[0]:.3f}, Y={plotter.picked_point[1]:.3f}, Z={plotter.picked_point[2]:.3f}\n")
    return plotter.picked_point

def downsample_mesh(mesh, target_ratio=0.5, preserve_edges=True):
    print("Downsampling mesh...")
    if isinstance(mesh, trimesh.Trimesh):
        # Simplify with quadric decimation
        target_faces = int(len(mesh.faces) * target_ratio)
        print(f"  Original faces: {len(mesh.faces)}")
        print(f"  Target faces: {target_faces}")
        simplified = mesh.simplify_quadric_decimation(target_faces)
        print(f"  Simplified faces: {len(simplified.faces)}")
        return simplified
    else:
        # Point cloud: voxel downsample
        cloud = pv.PolyData(mesh.vertices)
        downsampled = cloud.sample(voxel_size=0.01)
        return trimesh.PointCloud(downsampled.points)

def main(input_file, output_file, downsample=False, target_ratio=0.5, output_format=None):
    # Supported formats by trimesh
    SUPPORTED_FORMATS = ['stl', 'stl_ascii', 'ply', 'obj', 'off', 'glb', 'gltf', 'dae']

    # Load geometry
    geom = trimesh.load(input_file)

    # Handle Scene objects (multiple meshes)
    if isinstance(geom, trimesh.Scene):
        print("Loaded a scene with multiple meshes, concatenating into single mesh...")
        geom = trimesh.util.concatenate(list(geom.geometry.values()))

    # Detect or set output format
    if output_format is None:
        # Auto-detect from output filename
        output_format = output_file.split('.')[-1].lower()

    # Validate format
    if output_format not in SUPPORTED_FORMATS:
        print(f"\n[WARNING] Format '{output_format}' may not be supported.")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        print("Attempting to proceed anyway...\n")

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Output format: {output_format.upper()}")

    # Optional downsampling
    if downsample:
        geom = downsample_mesh(geom, target_ratio=target_ratio, preserve_edges=True)

    # Get points with detailed instructions
    vertices = geom.vertices if isinstance(geom, trimesh.Trimesh) else geom.points

    print("\n" + "#"*70)
    print("# COORDINATE SYSTEM ALIGNMENT PROCESS")
    print("#"*70)
    print("You will select 3 points to define a new coordinate system:")
    print("  1. ORIGIN: The center/reference point (0,0,0) of your coordinate system")
    print("  2. X-AXIS: A point along the positive X direction from origin")
    print("  3. Y-AXIS: A point along the positive Y direction (perpendicular to X)")
    print("The Z-axis will be computed automatically (right-hand rule)")
    print("#"*70 + "\n")

    origin = pick_points(geom,
                        "STEP 1/3: Select the ORIGIN point",
                        "Origin Point (0,0,0)\nThis is your reference point")

    x_point = pick_points(geom,
                         "STEP 2/3: Select a point along POSITIVE X direction",
                         "X-Axis Direction\nPick a point from origin\nalong desired +X axis")

    y_point = pick_points(geom,
                         "STEP 3/3: Select a point along POSITIVE Y direction",
                         "Y-Axis Direction\nPick a point perpendicular to X\nalong desired +Y axis")
   
    # Compute transformation
    print("\n" + "="*70)
    print("COMPUTING COORDINATE SYSTEM...")
    print("="*70)

    x_vec = (x_point - origin) / np.linalg.norm(x_point - origin)
    y_vec = (y_point - origin) / np.linalg.norm(y_point - origin)
    z_vec = np.cross(x_vec, y_vec)
    z_vec /= np.linalg.norm(z_vec)
    y_vec = np.cross(z_vec, x_vec) / np.linalg.norm(np.cross(z_vec, x_vec))

    # Display the computed coordinate system
    print("\nNew Coordinate System Vectors:")
    print(f"  Origin:  [{origin[0]:8.3f}, {origin[1]:8.3f}, {origin[2]:8.3f}]")
    print(f"  X-axis:  [{x_vec[0]:8.3f}, {x_vec[1]:8.3f}, {x_vec[2]:8.3f}] (normalized)")
    print(f"  Y-axis:  [{y_vec[0]:8.3f}, {y_vec[1]:8.3f}, {y_vec[2]:8.3f}] (normalized, orthogonalized)")
    print(f"  Z-axis:  [{z_vec[0]:8.3f}, {z_vec[1]:8.3f}, {z_vec[2]:8.3f}] (computed via cross product)")

    # Check orthogonality
    dot_xy = np.dot(x_vec, y_vec)
    dot_xz = np.dot(x_vec, z_vec)
    dot_yz = np.dot(y_vec, z_vec)
    print(f"\nOrthogonality check (should be close to 0):")
    print(f"  X·Y = {dot_xy:.6f}")
    print(f"  X·Z = {dot_xz:.6f}")
    print(f"  Y·Z = {dot_yz:.6f}")
    print("="*70 + "\n")

    # Rotation matrix
    R = np.column_stack((x_vec, y_vec, z_vec))
    print("Applying transformation to mesh...")
    transformed = (vertices - origin) @ R
   
    # Update geometry
    if isinstance(geom, trimesh.Trimesh):
        geom.vertices = transformed
    else:
        geom.points = transformed
   
    # Save with specified format
    print(f"\nSaving transformed mesh to {output_format.upper()} format...")
    try:
        geom.export(output_file, file_type=output_format)
        print(f"[SUCCESS] Transformed file saved successfully to: {output_file}")
        print(f"  Format: {output_format.upper()}")
    except Exception as e:
        print(f"[ERROR] Error saving file: {e}")
        print(f"  Attempting to save without explicit format...")
        geom.export(output_file)
        print(f"[SUCCESS] File saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python open3dv1.py <input_file> <output_file> [OPTIONS]")
        print("\nOptions:")
        print("  --downsample <ratio>    Downsample mesh (e.g., 0.5 for 50% faces)")
        print("  --format <format>       Output format")
        print("\nSupported export formats:")
        print("  - STL (.stl)            - Standard Tessellation Language (Binary)")
        print("  - STL ASCII (.stl_ascii) - Standard Tessellation Language (Text)")
        print("  - PLY (.ply)            - Polygon File Format")
        print("  - OBJ (.obj)            - Wavefront OBJ")
        print("  - OFF (.off)            - Object File Format")
        print("  - GLB (.glb)            - GL Transmission Format (Binary) [Recommended]")
        print("  - GLTF (.gltf)          - GL Transmission Format (JSON)")
        print("  - DAE (.dae)            - COLLADA")
        print("\nExamples:")
        print("  python open3dv1.py input.3mf output.stl")
        print("  python open3dv1.py input.obj output.glb --format glb")
        print("  python open3dv1.py input.3mf output.obj --downsample 0.3")
        print("  python open3dv1.py input.stl output.ply --format ply --downsample 0.5")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Parse optional arguments
    downsample = '--downsample' in sys.argv
    target_ratio = float(sys.argv[sys.argv.index('--downsample') + 1]) if downsample else 0.5

    output_format = None
    if '--format' in sys.argv:
        format_idx = sys.argv.index('--format')
        if format_idx + 1 < len(sys.argv):
            output_format = sys.argv[format_idx + 1].lower()

    main(input_file, output_file, downsample, target_ratio, output_format)