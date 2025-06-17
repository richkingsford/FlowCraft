import json
from flask import Flask, render_template, request, Markup, flash, redirect, url_for
from svg_generator import generate_svg # Assuming svg_generator.py is in the same directory
                                     # and app.py is run in a way that Python can find it.

app = Flask(__name__)
app.secret_key = 'super secret key' # Needed for flashing messages

def parse_workflow(json_string):
    """
    Parses a JSON string representing a workflow.
    (This function should already be defined as per previous steps)
    """
    try:
        workflow_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    if not isinstance(workflow_data, dict):
        raise ValueError("Invalid workflow format: The root element must be a dictionary.")

    if not workflow_data:
        raise ValueError("Invalid workflow format: The workflow dictionary cannot be empty.")

    # Get the first key (workflow name) and its corresponding steps
    # This assumes the first key is the main workflow.
    # A more robust solution might look for a specific key or structure if multiple top-level keys are possible.
    try:
        workflow_name = next(iter(workflow_data))
        steps = workflow_data[workflow_name]
    except StopIteration: # Handles empty dictionary case if not caught by `if not workflow_data`
        raise ValueError("Invalid workflow format: Workflow dictionary is structured unexpectedly or empty.")


    if not isinstance(steps, list):
        raise ValueError(f"Invalid workflow format: Steps for '{workflow_name}' must be a list.")

    return steps


@app.route('/', methods=['GET'])
def index():
    """Serves the main page with the upload form."""
    return render_template('index.html', svg_output=None)

@app.route('/generate', methods=['POST'])
def generate_diagram():
    """
    Handles the workflow JSON file upload, parses it, generates the SVG,
    and re-renders the main page with the diagram or error messages.
    """
    if 'workflow_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['workflow_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file:
        try:
            json_string = file.read().decode('utf-8')

            # Collect visual parameters from form data, with defaults.
            # These are passed to the svg_generator module.
            visual_params = {
                'node_width': int(request.form.get('node_width', 150)),
                'node_height': int(request.form.get('node_height', 75)), # This is min_node_height in svg_generator
                'text_padding': int(request.form.get('text_padding', 10)), # Standardized from 'padding'
                'margin': int(request.form.get('margin', 40)),
                'line_height_px': int(request.form.get('line_height_px', 18)),
                'chars_per_line_approx': int(request.form.get('chars_per_line_approx', 17)), # (150-20)/8 approx
                'fill_color_action': request.form.get('fill_color_action', '#ADD8E6'),
                'fill_color_decision': request.form.get('fill_color_decision', '#FFFFE0'),
                'text_color': request.form.get('text_color', '#000000'),
                'border_color': request.form.get('border_color', '#000000'),
                'line_color': request.form.get('line_color', '#333333'),
                'arrow_size': int(request.form.get('arrow_size', 10)),
            }

            parsed_workflow = parse_workflow(json_string)
            svg_content = generate_svg(parsed_workflow, visual_params)
            return render_template('index.html', svg_output=Markup(svg_content))

        except ValueError as e:
            flash(f'Error processing workflow: {str(e)}')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}')
            return redirect(url_for('index'))

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Note: This simple app.run() is for development.
    # For production, use a WSGI server like Gunicorn or Waitress.
    app.run(debug=True)
