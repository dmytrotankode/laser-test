import sys
import pyiges
import pyvista as pv

def convert_igs_to_stl(igs_path, stl_path):
    print(f"Reading {igs_path}...")
    try:
        iges = pyiges.read(igs_path)
        print("Converting to mesh...")
        
        # We want to extract surfaces and convert them to a polygonal mesh
        # pyiges parses B-spline surfaces. to_vtk creates a PyVista MultiBlock or PolyData
        mesh = iges.to_vtk(bsplines=True, surfaces=True, merge=True)
        
        # If it's a MultiBlock, we need to extract the PolyData
        if isinstance(mesh, pv.MultiBlock):
            # Combine blocks into a single PolyData
            blocks = []
            for block in mesh:
                if block is not None and isinstance(block, pv.PolyData):
                    blocks.append(block)
                elif block is not None and isinstance(block, pv.UnstructuredGrid):
                    blocks.append(block.extract_surface())
            if not blocks:
                print("No valid surface blocks found!")
                sys.exit(1)
            
            combined = blocks[0]
            for b in blocks[1:]:
                combined = combined.merge(b)
            mesh = combined
        elif isinstance(mesh, pv.UnstructuredGrid):
            mesh = mesh.extract_surface()
            
        print(f"Saving to {stl_path}...")
        mesh.save(stl_path)
        print("Done!")
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)

if __name__ == '__main__':
    igs_file = r"c:\__TARAS_\__DISTI__\laser-test\service_5052\input\model_3d\Tor XL_176 _2.IGS"
    stl_file = r"c:\__TARAS_\__DISTI__\laser-test\service_5052\input\model_3d\helmet_ref.stl"
    convert_igs_to_stl(igs_file, stl_file)
