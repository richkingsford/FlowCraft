import unittest
import os
import shutil
import json
from generate_diagrams import generate_diagrams_from_json, local_parse_workflow

class TestGenerateDiagrams(unittest.TestCase):

    def setUp(self):
        """Set up test environment; create a temporary workflows directory."""
        self.test_workflows_dir = "temp_test_workflows"
        self.source_workflows_dir = "workflows" # Where the original 'dark mode testing.json' is
        os.makedirs(self.test_workflows_dir, exist_ok=True)

        # Copy the existing workflow file to the temporary directory for testing
        self.original_workflow_file = "dark mode testing.json"
        self.source_file_path = os.path.join(self.source_workflows_dir, self.original_workflow_file)
        self.test_workflow_file_path = os.path.join(self.test_workflows_dir, self.original_workflow_file)

        if os.path.exists(self.source_file_path):
            shutil.copy(self.source_file_path, self.test_workflow_file_path)
        else:
            # Create a minimal valid file if the source doesn't exist, to ensure tests can run
            # This is a fallback, ideally the file from the user request should be available
            minimal_workflow = {
                "MinimalProcess": [
                    {"stepID": "1", "type": "action", "name": "Minimal Action", "nextStepID": "end"},
                    {"stepID": "end", "type": "terminal", "name": "End"}
                ]
            }
            with open(self.test_workflow_file_path, 'w') as f:
                json.dump(minimal_workflow, f)


        # Create a known invalid JSON file
        self.invalid_json_path = os.path.join(self.test_workflows_dir, "invalid.json")
        with open(self.invalid_json_path, 'w') as f:
            f.write("{'bad_json': True,}") # Invalid JSON due to single quotes and trailing comma

        # Create a JSON file with valid JSON structure but invalid workflow content (e.g., missing stepID)
        self.invalid_workflow_path = os.path.join(self.test_workflows_dir, "invalid_workflow.json")
        invalid_workflow_content = {
            "BadWorkflow": [
                {"type": "action", "name": "Missing ID"}
            ]
        }
        with open(self.invalid_workflow_path, 'w') as f:
            json.dump(invalid_workflow_content, f)

        # Create a non-JSON file
        self.non_json_path = os.path.join(self.test_workflows_dir, "not_a_json.txt")
        with open(self.non_json_path, 'w') as f:
            f.write("This is not a JSON file.")


    def tearDown(self):
        """Clean up test environment; remove the temporary directory."""
        if os.path.exists(self.test_workflows_dir):
            shutil.rmtree(self.test_workflows_dir)

    def test_local_parse_workflow_valid(self):
        """Test parsing of a valid workflow JSON string."""
        valid_json_string = """
        {
          "TestProcess": [
            {
              "stepID": "1",
              "type": "action",
              "name": "Action 1",
              "nextStepID": "2"
            },
            {
              "stepID": "2",
              "type": "terminal",
              "name": "End"
            }
          ]
        }
        """
        expected_steps = [
            {"stepID": "1", "type": "action", "name": "Action 1", "nextStepID": "2"},
            {"stepID": "2", "type": "terminal", "name": "End"}
        ]
        parsed_steps = local_parse_workflow(valid_json_string)
        self.assertEqual(parsed_steps, expected_steps)

    def test_local_parse_workflow_invalid_json(self):
        """Test parsing of an invalid JSON string."""
        invalid_json_string = "{'bad_json': True,}"
        with self.assertRaisesRegex(ValueError, "Invalid JSON format"):
            local_parse_workflow(invalid_json_string)

    def test_local_parse_workflow_invalid_structure(self):
        """Test parsing of JSON with invalid workflow structure."""
        invalid_structure_string = '{"RootKey": {"not_a_list": "data"}}'
        with self.assertRaisesRegex(ValueError, "must be a list"):
            local_parse_workflow(invalid_structure_string)

        empty_dict_string = '{}'
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            local_parse_workflow(empty_dict_string)

        missing_stepid_string = '{"Workflow": [{"name": "Step without ID"}]}'
        with self.assertRaisesRegex(ValueError, "Each step must be a dictionary with 'stepID' and 'name'"):
            local_parse_workflow(missing_stepid_string)


    def test_generate_diagrams_from_json_creates_svg(self):
        """Test that an SVG file is created for a valid JSON workflow."""
        generate_diagrams_from_json(self.test_workflows_dir)
        expected_svg_filename = os.path.splitext(self.original_workflow_file)[0] + ".svg"
        expected_svg_path = os.path.join(self.test_workflows_dir, expected_svg_filename)
        self.assertTrue(os.path.exists(expected_svg_path), f"SVG file '{expected_svg_path}' was not created.")

        # Check if SVG content is non-empty and looks like SVG
        with open(expected_svg_path, 'r') as f:
            content = f.read()
        self.assertTrue(content.strip().startswith("<svg"))
        self.assertTrue(content.strip().endswith("</svg>"))


    def test_generate_diagrams_handles_invalid_json_file(self):
        """Test that an invalid JSON file is skipped and does not create an SVG."""
        generate_diagrams_from_json(self.test_workflows_dir)
        invalid_svg_path = os.path.join(self.test_workflows_dir, "invalid.svg")
        self.assertFalse(os.path.exists(invalid_svg_path), "SVG file created for invalid JSON.")

    def test_generate_diagrams_handles_invalid_workflow_content(self):
        """Test that a file with invalid workflow structure is skipped."""
        generate_diagrams_from_json(self.test_workflows_dir)
        invalid_workflow_svg_path = os.path.join(self.test_workflows_dir, "invalid_workflow.svg")
        self.assertFalse(os.path.exists(invalid_workflow_svg_path), "SVG file created for invalid workflow structure.")

    def test_generate_diagrams_ignores_non_json_files(self):
        """Test that non-JSON files are ignored."""
        generate_diagrams_from_json(self.test_workflows_dir)
        non_json_svg_path = os.path.join(self.test_workflows_dir, "not_a_json.svg")
        self.assertFalse(os.path.exists(non_json_svg_path), "SVG file created for non-JSON file.")

    def test_generate_diagrams_no_json_files(self):
        """Test behavior when the workflows directory contains no JSON files."""
        # Create an empty subdirectory for this test
        empty_dir = os.path.join(self.test_workflows_dir, "empty_subdir")
        os.makedirs(empty_dir, exist_ok=True)
        generate_diagrams_from_json(empty_dir) # Should run without error and produce no output files
        self.assertEqual(len(os.listdir(empty_dir)), 0, "Files were created in an empty directory.")

    def test_generate_diagrams_nonexistent_directory(self):
        """Test behavior with a non-existent workflows directory."""
        # This should print an error but not raise an exception that stops the test runner.
        # We can capture stdout/stderr if needed, but for now, just ensuring it doesn't crash.
        generate_diagrams_from_json("non_existent_directory_for_test")
        # No assertion needed other than it doesn't crash the test suite.
        # The function itself prints an error message.

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
