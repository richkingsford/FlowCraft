import os
import json
import sys

# Add the workflow_visualizer directory to the Python path
# to allow importing modules from it.
current_dir = os.path.dirname(os.path.abspath(__file__))
workflow_visualizer_dir = os.path.join(current_dir, "workflow_visualizer")
sys.path.insert(0, workflow_visualizer_dir)

try:
    from svg_generator import generate_svg
    # parse_workflow is in app.py, which might have Flask dependencies.
    # For simplicity in this standalone script, we'll re-implement a focused parser.
except ImportError as e:
    print(f"Error importing from workflow_visualizer: {e}")
    print("Please ensure that 'workflow_visualizer' directory is in the same directory as this script,")
    print("and that svg_generator.py exists within it.")
    sys.exit(1)

def local_parse_workflow(json_string):
    """
    Parses a JSON string representing a workflow.
    This is a simplified version, assuming the structure found in `dark mode testing.json`.
    """
    try:
        workflow_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    if not isinstance(workflow_data, dict):
        raise ValueError("Invalid workflow format: The root element must be a dictionary.")

    if not workflow_data:
        raise ValueError("Invalid workflow format: The workflow dictionary cannot be empty.")

    # Attempt to get the first key's value, assuming it's the list of steps
    try:
        workflow_name = next(iter(workflow_data))
        steps = workflow_data[workflow_name]
    except StopIteration:
        raise ValueError("Invalid workflow format: Workflow dictionary is structured unexpectedly or empty.")

    if not isinstance(steps, list):
        raise ValueError(f"Invalid workflow format: Steps for '{workflow_name}' must be a list.")

    # Basic validation of step structure (can be expanded)
    for step in steps:
        if not isinstance(step, dict) or "stepID" not in step or "name" not in step:
            raise ValueError(f"Invalid step format: {step}. Each step must be a dictionary with 'stepID' and 'name'.")
    return steps

def generate_diagrams_from_json(workflows_dir="workflows"):
    """
    Scans a directory for JSON workflow files and generates SVG diagrams for each.

    Args:
        workflows_dir (str): The directory containing JSON workflow files.
                             SVG files will also be saved here.
    """
    if not os.path.isdir(workflows_dir):
        print(f"Error: Directory '{workflows_dir}' not found.")
        return

    print(f"Scanning for JSON files in '{workflows_dir}'...")
    generated_count = 0
    error_count = 0

    for filename in os.listdir(workflows_dir):
        if filename.endswith(".json"):
            json_filepath = os.path.join(workflows_dir, filename)
            svg_filename = os.path.splitext(filename)[0] + ".svg"
            svg_filepath = os.path.join(workflows_dir, svg_filename)

            print(f"Processing '{json_filepath}'...")
            try:
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    json_string = f.read()

                parsed_workflow = local_parse_workflow(json_string)

                # Visual parameters can be customized here if needed,
                # otherwise svg_generator will use its defaults.
                visual_params = {}

                svg_content = generate_svg(parsed_workflow, visual_params)

                with open(svg_filepath, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                print(f"Successfully generated '{svg_filepath}'")
                generated_count += 1
            except ValueError as e:
                print(f"Skipping '{filename}' due to parsing error: {e}")
                error_count += 1
            except Exception as e:
                print(f"Skipping '{filename}' due to an unexpected error during generation: {e}")
                error_count += 1

    print("\n--- Generation Summary ---")
    print(f"Successfully generated diagrams: {generated_count}")
    print(f"Files skipped due to errors: {error_count}")

if __name__ == "__main__":
    # Determine the base directory of the script to correctly locate the 'workflows' folder
    # and 'workflow_visualizer'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workflows_folder = os.path.join(base_dir, "workflows")

    # Adjust sys.path for imports if workflow_visualizer is not in the same directory as the script's execution path
    # The lines at the top of the script already handle adding workflow_visualizer to sys.path
    # relative to this script's location.

    generate_diagrams_from_json(workflows_folder)
