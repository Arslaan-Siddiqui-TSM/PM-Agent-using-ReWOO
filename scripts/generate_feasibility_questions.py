import os
import glob
from src.app.feasibility_agent import run_feasibility_agent

if __name__ == "__main__":
    import time
    # Automatically get all PDF files from the files directory
    files_dir = "data/files"
    sample_files = glob.glob(os.path.join(files_dir, "*.pdf"))
    
    if not sample_files:
        print(f"No PDF files found in {files_dir} directory")
    else:
        print(f"Found {len(sample_files)} PDF files:")
        for file in sample_files:
            print(f"  - {file}")
        start_time = time.perf_counter()
        run_feasibility_agent(sample_files)
        print(f"Feasibility assessment generated in {time.perf_counter() - start_time:.2f} seconds")