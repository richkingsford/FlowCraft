# Workflow Visualizer

A Flask-based web application to dynamically generate SVG diagrams from workflow descriptions provided in JSON format. This tool allows users to visualize complex processes, customize the appearance of the diagram, and download the resulting SVG.

## Features

*   **JSON to SVG Conversion**: Parses workflow data from a JSON file and renders it as an SVG diagram.
*   **Web Interface**: User-friendly UI for uploading JSON files and adjusting visual parameters.
*   **Customizable Visuals**: Control node size, colors, margins, padding, text properties, and more through the UI.
*   **Text Wrapping**: Node names automatically wrap to fit within the node width.
*   **Dynamic Node Height**: Node height adjusts based on the content (text lines).
*   **Decision Node Support**: Differentiates 'action' and 'decision' nodes, displaying branches for decisions.
*   **Arrow Connectors**: Nodes are connected with lines and arrowheads to indicate flow.
*   **SVG Download**: Generated diagrams can be downloaded as `.svg` files.
*   **Error Handling**: Gracefully handles missing steps in JSON connections and provides feedback for invalid JSON.

## Project Structure

*   `app.py`: Main Flask application file. Handles routing, request processing, and interaction with the SVG generator.
*   `svg_generator.py`: Module responsible for generating the SVG diagram from parsed workflow data and visual parameters.
*   `requirements.txt`: Lists Python dependencies (Flask, svgwrite).
*   `sample_workflow.json`: An example JSON file demonstrating the expected workflow structure.
*   `templates/`: Directory containing HTML templates.
    *   `index.html`: The main page template with the upload form, UI controls, and SVG display area.
*   `static/`: Directory for static files.
    *   `styles.css`: CSS file for styling the web interface.

## Setup

1.  **Get the Files**:
    *   If this project is in a Git repository, clone it: `git clone <repository_url>`
    *   Otherwise, ensure all project files are downloaded/copied into a local directory named `workflow_visualizer`.

2.  **Create a Python Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    Navigate to the `workflow_visualizer` directory (where `requirements.txt` is located) and run:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Navigate to the `workflow_visualizer` directory.
3.  Run the Flask development server:
    ```bash
    python app.py
    ```
4.  The application will typically be available at `http://127.0.0.1:5000/`.

## Usage

1.  Open your web browser and go to `http://127.0.0.1:5000/`.
2.  **Upload JSON**: Click the "Choose File" button and select your workflow JSON file. You can use `sample_workflow.json` provided with this project as an example.
3.  **Adjust Parameters**: Modify the visual parameters (node width, colors, etc.) using the UI controls as needed. Default values are pre-filled.
4.  **Generate**: Click the "Generate Diagram" button.
5.  **View & Download**: The generated SVG diagram will appear on the page. If you wish to save it, click the "Download SVG" button.

## JSON Format

The application expects a JSON file with a main key (e.g., "QA_Process") whose value is an array of step objects. Each step object should have the following structure:

*   `stepID` (String): A unique identifier for the step.
*   `type` (String): The type of node. Can be `"action"` or `"decision"`.
*   `name` (String): The text to be displayed within the node.
*   `nextStepID` (String, Optional): The `stepID` of the next step in the workflow.
    *   For `action` nodes, this directly points to the next step.
    *   For `decision` nodes, this field is typically omitted, and flow is defined by `options`.
    *   A special value `"previous_decision"` for `nextStepID` indicates a loop back in the process (currently, this node type will not draw an outgoing arrow; its role is as a target for decision branches).
*   `options` (Array, Required for `decision` nodes): An array of option objects, each defining a branch from the decision.
    *   `decisionText` (String): Text to label the connection line for this option (e.g., "Yes", "No").
    *   `nextStepID` (String): The `stepID` of the step this option leads to.

Refer to `sample_workflow.json` for a concrete example.

```json
{
  "WORKFLOW_NAME": [
    {
      "stepID": "unique_id_1",
      "type": "action",
      "name": "Description of action",
      "nextStepID": "unique_id_2"
    },
    {
      "stepID": "unique_id_2",
      "type": "decision",
      "name": "Decision point question?",
      "options": [
        {
          "decisionText": "Outcome A",
          "nextStepID": "unique_id_3"
        },
        {
          "decisionText": "Outcome B",
          "nextStepID": "unique_id_4"
        }
      ]
    }
    // ... more steps
  ]
}
```
