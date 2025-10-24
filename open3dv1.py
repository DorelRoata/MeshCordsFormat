import trimesh
import pyvista as pv
import numpy as np
import sys
import tkinter as tk

def pick_points(geom, prompt, instruction_text=None, step_info=""):
    print("\n" + "="*70)
    print(prompt)
    if instruction_text:
        print(instruction_text)
    print("="*70)
    print("CONTROLS:")
    print("  - Click on the mesh to select a point")
    print("  - Click 'CONFIRM & NEXT' button (lower right) to continue")
    print("  - Alternative: Press 'N' or ENTER key")
    print("")
    print("CAMERA CONTROLS:")
    print("  - Rotate: Left mouse button + drag")
    print("  - Pan: Middle mouse button or Shift + Left mouse")
    print("  - Zoom: Mouse wheel or Right mouse button")
    print("="*70 + "\n")

    # Create plotter with window position centered
    plotter = pv.Plotter(window_size=[1200, 800])

    # Convert geometry to PyVista format
    if isinstance(geom, trimesh.Trimesh):
        faces = np.column_stack([np.full(len(geom.faces), 3), geom.faces]).flatten()
        mesh = pv.PolyData(np.asarray(geom.vertices), faces=faces)
    else:
        mesh = pv.PolyData(np.asarray(geom.vertices))

    plotter.add_mesh(mesh, color='lightgray', opacity=0.9, lighting=True)

    # Add title at the top with better formatting
    title_text = f"{step_info}\n{prompt}"
    plotter.add_text(title_text, position='upper_edge', font_size=15, color='navy', font='arial')

    # Add instruction box in upper right (separate from title)
    if instruction_text:
        instruction_box = f"{instruction_text}\n\nClick on mesh to select point"
        plotter.add_text(instruction_box, position='upper_right', font_size=11, color='darkslategray', font='arial')

    # Add coordinate axes for reference
    plotter.add_axes(interactive=True, line_width=3, cone_radius=0.4)

    # State tracking
    selected_point = {'point': None, 'confirmed': False}
    coord_text_actor = None
    sphere_actor = None

    def callback(picked_point):
        nonlocal coord_text_actor, sphere_actor
        selected_point['point'] = picked_point

        # Remove old coordinate text if exists
        if coord_text_actor is not None:
            plotter.remove_actor(coord_text_actor)

        # Remove old sphere marker if exists
        if sphere_actor is not None:
            plotter.remove_actor(sphere_actor)

        # Add sphere at picked point for visual feedback
        sphere = pv.Sphere(radius=mesh.length * 0.005, center=picked_point)
        sphere_actor = plotter.add_mesh(sphere, color='orangered', opacity=1.0)

        # Add coordinate text in bottom left with better formatting
        coord_text = (f"SELECTED POINT:\n"
                     f"X: {picked_point[0]:10.3f}\n"
                     f"Y: {picked_point[1]:10.3f}\n"
                     f"Z: {picked_point[2]:10.3f}")
        coord_text_actor = plotter.add_text(
            coord_text,
            position='lower_left',
            font_size=6,
            color='black',
            font='courier'
        )

        print(f"Point selected: X={picked_point[0]:.3f}, Y={picked_point[1]:.3f}, Z={picked_point[2]:.3f}")

    # Button callback to confirm selection
    def confirm_selection():
        if selected_point['point'] is not None:
            selected_point['confirmed'] = True
            plotter.close()
        else:
            print("Please select a point first!")

    # Enable point picking with better visual feedback
    plotter.enable_point_picking(
        callback=callback,
        show_message=False,  # Disable default message to avoid overlap
        color='red',
        point_size=25,
        tolerance=0.025
    )

    # Create a proper button widget
    button_triggered = {'value': False}

    # Create a 2D box in the lower part of the screen to act as a button
    # We'll use a plane positioned in screen coordinates
    import vtk

    # Create button representation using a 2D rectangle
    button_actor = vtk.vtkActor2D()
    button_mapper = vtk.vtkPolyDataMapper2D()

    # Create a rectangle for the button
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(4)
    # Position in pixel coordinates (will be in lower center)
    # These will be set dynamically based on window size

    polygon = vtk.vtkPolygon()
    polygon.GetPointIds().SetNumberOfIds(4)
    for i in range(4):
        polygon.GetPointIds().SetId(i, i)

    polygons = vtk.vtkCellArray()
    polygons.InsertNextCell(polygon)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(polygons)

    button_mapper.SetInputData(polydata)
    button_actor.SetMapper(button_mapper)
    button_actor.GetProperty().SetColor(0.18, 0.55, 0.34)  # Green color (RGB)

    # Update button position based on window size
    def update_button_position():
        render_window = plotter.render_window
        if render_window:
            width, height = render_window.GetSize()
            # Center the button horizontally, place near bottom
            btn_width = 300
            btn_height = 60
            x_start = (width - btn_width) // 2
            y_start = 30

            points.SetPoint(0, x_start, y_start, 0)
            points.SetPoint(1, x_start + btn_width, y_start, 0)
            points.SetPoint(2, x_start + btn_width, y_start + btn_height, 0)
            points.SetPoint(3, x_start, y_start + btn_height, 0)
            points.Modified()

    # Add the button actor to renderer
    plotter.renderer.AddActor2D(button_actor)

    # Add text on top of button
    button_text_actor = vtk.vtkTextActor()
    button_text_actor.SetInput("CONFIRM & CONTINUE")
    button_text_actor.GetTextProperty().SetFontSize(18)
    button_text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)  # White
    button_text_actor.GetTextProperty().SetBold(True)
    button_text_actor.GetTextProperty().SetJustificationToCentered()
    button_text_actor.GetTextProperty().SetVerticalJustificationToCentered()

    def update_button_text_position():
        render_window = plotter.render_window
        if render_window:
            width, height = render_window.GetSize()
            btn_width = 300
            btn_height = 60
            x_start = (width - btn_width) // 2
            y_start = 30
            # Center the text in the button
            button_text_actor.SetPosition(x_start + btn_width // 2, y_start + btn_height // 2)

    plotter.renderer.AddActor2D(button_text_actor)

    # Update positions initially
    update_button_position()
    update_button_text_position()

    # Click detection
    def check_button_click(iren, event_name):
        if button_triggered['value']:
            return

        click_pos = iren.GetEventPosition()
        window_size = iren.GetRenderWindow().GetSize()

        # Button bounds (center horizontally, near bottom)
        btn_width = 300
        btn_height = 60
        x_start = (window_size[0] - btn_width) // 2
        y_start = 30

        if (x_start <= click_pos[0] <= x_start + btn_width and
            y_start <= click_pos[1] <= y_start + btn_height):

            if selected_point['point'] is None:
                print("Please select a point first!")
                return

            button_triggered['value'] = True

            # Change button color to darker green
            button_actor.GetProperty().SetColor(0.1, 0.37, 0.2)

            # Change text
            button_text_actor.SetInput("✓ CONFIRMED")
            button_text_actor.GetTextProperty().SetColor(0.7, 1.0, 0.7)

            iren.GetRenderWindow().Render()
            print("\n>>> BUTTON CLICKED - Moving to next step...")
            selected_point['confirmed'] = True

            # Close the plotter
            import time
            time.sleep(0.1)
            try:
                iren.TerminateApp()
            except:
                plotter.close()

    plotter.iren.add_observer('LeftButtonPressEvent', check_button_click)

    # Add keyboard shortcuts as alternative
    def on_key_press_n():
        confirm_selection()

    def on_key_press_enter():
        confirm_selection()

    plotter.add_key_event('n', on_key_press_n)
    plotter.add_key_event('Return', on_key_press_enter)

    # Try to center the window before showing
    try:
        # Get screen dimensions
        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate centered position
        window_width = 1200
        window_height = 800
        x = max(0, (screen_width - window_width) // 2)
        y = max(0, (screen_height - window_height) // 2)

        # Properly destroy Tkinter root
        root.quit()
        root.destroy()
        del root

        # Set window position before showing (if render window exists)
        if hasattr(plotter, 'ren_win') and plotter.ren_win:
            plotter.ren_win.SetPosition(x, y)
    except Exception as e:
        # If centering fails, just continue (window will appear at default position)
        print(f"[DEBUG] Window centering failed: {e}")
        pass

    # Show the plotter
    print(f"[DEBUG] Opening window for: {prompt[:50]}...")
    plotter.show()
    print(f"[DEBUG] Window closed")

    # Validate that a point was selected and confirmed
    if not selected_point['confirmed'] or selected_point['point'] is None:
        raise ValueError("No point selected or selection not confirmed.")

    final_point = selected_point['point']
    print(f"CONFIRMED: X={final_point[0]:.3f}, Y={final_point[1]:.3f}, Z={final_point[2]:.3f}\n")

    return final_point

def downsample_mesh(mesh, target_ratio=0.5, preserve_edges=True):
    print("Downsampling mesh...")
    if isinstance(mesh, trimesh.Trimesh):
        target_faces = int(len(mesh.faces) * target_ratio)
        print(f"  Original faces: {len(mesh.faces)}")
        print(f"  Target faces: {target_faces}")

        # Try multiple downsampling methods in order of preference
        try:
            # Method 1: Quadric decimation (requires fast_simplification)
            simplified = mesh.simplify_quadric_decimation(target_faces)
            print(f"  Simplified faces: {len(simplified.faces)}")
            print("  Method: Quadric decimation")
            return simplified
        except (ImportError, ModuleNotFoundError) as e:
            print(f"  [INFO] Quadric decimation unavailable: {e}")
            print("  [INFO] Falling back to vertex clustering method...")

            # Method 2: Vertex clustering (built-in, no dependencies)
            try:
                # Calculate appropriate voxel size based on mesh bounds and target ratio
                bounds = mesh.bounds
                diagonal = np.linalg.norm(bounds[1] - bounds[0])
                # Estimate voxel size to achieve target face count
                voxel_size = diagonal * (1.0 - target_ratio) * 0.1
                simplified = mesh.simplify_vertex_clustering(voxel_size=voxel_size)
                print(f"  Simplified faces: {len(simplified.faces)}")
                print(f"  Method: Vertex clustering (voxel_size={voxel_size:.4f})")
                return simplified
            except Exception as e2:
                print(f"  [WARNING] Vertex clustering failed: {e2}")
                print("  [WARNING] Returning original mesh without downsampling")
                return mesh
        except Exception as e:
            print(f"  [WARNING] Downsampling failed: {e}")
            print("  [WARNING] Returning original mesh without downsampling")
            return mesh
    else:
        # Point cloud: voxel downsample
        try:
            cloud = pv.PolyData(mesh.vertices)
            downsampled = cloud.sample(voxel_size=0.01)
            return trimesh.PointCloud(downsampled.points)
        except Exception as e:
            print(f"  [WARNING] Point cloud downsampling failed: {e}")
            return mesh

def main(input_file, output_file, downsample=False, target_ratio=0.5, output_format=None):
    # Supported formats by trimesh
    SUPPORTED_FORMATS = ['stl', 'stl_ascii', 'ply', 'obj', 'off', 'glb', 'gltf', 'dae']

    # Check for optional dependencies if downsampling is enabled
    if downsample:
        try:
            import fast_simplification
        except ImportError:
            print("\n" + "="*70)
            print("[INFO] Optional dependency 'fast_simplification' not found")
            print("       Using built-in vertex clustering method instead")
            print("       For better quality downsampling, install with:")
            print("       pip install fast-simplification")
            print("="*70 + "\n")

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
                        "Select the ORIGIN point",
                        "Origin Point (0,0,0)\nThis is your reference point",
                        step_info="STEP 1 of 3")

    x_point = pick_points(geom,
                         "Select a point along POSITIVE X direction",
                         "X-Axis Direction\nPick a point from origin\nalong desired +X axis",
                         step_info="STEP 2 of 3")

    y_point = pick_points(geom,
                         "Select a point along POSITIVE Y direction",
                         "Y-Axis Direction\nPick a point perpendicular to X\nalong desired +Y axis",
                         step_info="STEP 3 of 3")
   
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