import svgwrite
import math

def get_connection_points(source_node, target_node, nodes_map):
    """
    Calculates visually appropriate connection points between two nodes.
    source_node and target_node are dicts from nodes_map.
    Returns (x1, y1, x2, y2)
    """
    s_id, s_data = source_node
    t_id, t_data = target_node

    s_x, s_y, s_w, s_h = s_data['x'], s_data['y'], s_data['width'], s_data['height']
    t_x, t_y, t_w, t_h = t_data['x'], t_data['y'], t_data['width'], t_data['height']

    # Points: tc (top-center), bc (bottom-center), lc (left-center), rc (right-center)
    s_points = {
        'tc': (s_x + s_w / 2, s_y),
        'bc': (s_x + s_w / 2, s_y + s_h),
        'lc': (s_x, s_y + s_h / 2),
        'rc': (s_x + s_w, s_y + s_h / 2),
    }
    t_points = {
        'tc': (t_x + t_w / 2, t_y),
        'bc': (t_x + t_w / 2, t_y + t_h),
        'lc': (t_x, t_y + t_h / 2),
        'rc': (t_x + t_w, t_y + t_h / 2),
    }

    # Default: source bottom-center to target top-center (for vertical flow)
    x1, y1 = s_points['bc']
    x2, y2 = t_points['tc']

    # Basic heuristic for better routing if target is to the side or above
    # If target is significantly to the right
    if t_x > s_x + s_w + 20 : # 20 is a buffer
        x1, y1 = s_points['rc']
        x2, y2 = t_points['lc']
    # If target is significantly to the left
    elif t_x < s_x - t_w - 20:
        x1, y1 = s_points['lc']
        x2, y2 = t_points['rc']
    # If target is above (e.g. loop back)
    elif t_y + t_h < s_y:
        x1, y1 = s_points['tc'] # From top of source
        x2, y2 = t_points['bc'] # To bottom of target

    return x1, y1, x2, y2


def generate_svg(workflow_data, visual_params=None):
    """
    Generates an SVG representation of a workflow.

    Args:
        workflow_data (list): A list of step objects parsed from the JSON input.
                              Each step is a dictionary defining its properties.
        visual_params (dict, optional): A dictionary of visual parameters to customize
                                       the SVG output. Defaults are used if not provided.

    Returns:
        str: The generated SVG diagram as an XML string.
    """
    if visual_params is None:
        visual_params = {}

    # --- Parameter Setup ---
    # Node dimensions and spacing
    node_width = visual_params.get('node_width', 150)
    min_node_height = visual_params.get('node_height', 75) # Minimum height, can grow with text
    text_padding = visual_params.get('text_padding', 10) # Internal padding for text within a node
    margin = visual_params.get('margin', 40) # Margin between nodes

    # Colors
    fill_color_action = visual_params.get('fill_color_action', '#ADD8E6')
    fill_color_decision = visual_params.get('fill_color_decision', '#FFFFE0')
    text_color = visual_params.get('text_color', '#000000')
    border_color = visual_params.get('border_color', '#000000')
    line_color = visual_params.get('line_color', '#333333') # Connector line color

    # Text and line properties
    line_height_px = visual_params.get('line_height_px', 18) # Approx height of one line of text
    arrow_size = visual_params.get('arrow_size', 10) # Size of the arrowhead marker

    # Character wrapping: Calculate how many chars fit per line based on node_width and padding.
    # The divisor (e.g., 8) is an approximation of average character width; might need adjustment for different fonts/sizes.
    default_chars_per_line = (node_width - (2 * text_padding)) // 8
    chars_per_line_approx = visual_params.get('chars_per_line_approx', default_chars_per_line)
    # --- End Parameter Setup ---

    # Initialize SVG drawing object with a default size.
    # This size will be dynamically adjusted at the end based on content.
    dwg = svgwrite.Drawing(size=('800px', '600px'))

    # Define an arrowhead marker for connector lines.
    # This marker is added to the <defs> section of the SVG and can be referenced by ID.
    arrowhead = dwg.marker(
        insert=(arrow_size, arrow_size / 2),  # Tip of the arrow at the center of the marker viewbox y-coordinate
        size=(arrow_size, arrow_size),        # Viewbox size of the marker
        orient='auto',                        # Rotates the marker to align with the line direction
        markerUnits='strokeWidth'             # Scales marker with line stroke width (optional)
    )
    arrowhead.add(dwg.path(d=f"M0,0 L{arrow_size},{arrow_size/2} L0,{arrow_size} z", fill=line_color)) # Triangle path
    dwg.defs.add(arrowhead) # Add marker to <defs>

    # --- Layout Variables ---
    current_y = margin # Running y-coordinate for placing nodes vertically
    max_x_pos = 0      # Tracks the maximum x-coordinate reached, for dynamic SVG width
    nodes_map = {}     # Stores details of each node (id, position, dimensions, type) for easy lookup during connection drawing.
                       # Format: {step_id: {'x': x, 'y': y, 'width': w, 'height': h, 'type': type, ...}}
    # --- End Layout Variables ---

    # --- First Pass: Node Rendering and Information Gathering ---
    # Iterate through each step in the workflow data to draw nodes and store their info.
    # This simple layout places nodes vertically, one after another.
    for i, step in enumerate(workflow_data):
        step_id = step.get('stepID', f"node_{i}") # Use provided stepID or generate a fallback
        step_name = step.get('name', 'Unnamed Step') # Node label
        step_type = step.get('type', 'action')       # Node type ('action' or 'decision')

        # --- Text Wrapping Logic ---
        # Split the node's name into words and arrange them into lines
        # that fit within the node's width (minus padding).
        words = step_name.split()
        lines = []
        current_line_text = ""
        for word in words:
            if not current_line_text:
                current_line_text = word
            elif len(current_line_text) + len(word) + 1 <= chars_per_line_approx:
                current_line_text += " " + word
            else:
                lines.append(current_line_text)
                current_line_text = word
        if current_line_text:
            lines.append(current_line_text)

        num_lines = len(lines)
        # Calculate dynamic node height based on number of text lines and padding.
        current_node_height = max(min_node_height, (num_lines * line_height_px) + (2 * text_padding))
        # --- End Text Wrapping Logic ---

        # Node position (simple vertical stack for now)
        x_pos = margin

        # Store node information for the second pass (drawing connections)
        nodes_map[step_id] = {
            'x': x_pos, 'y': current_y,
            'width': node_width, 'height': current_node_height,
            'type': step_type, 'name': step_name,
            'step_data': step # Keep original step data for reference
        }

        # Determine fill color based on node type
        fill_color = fill_color_action if step_type == 'action' else fill_color_decision

        # Draw the node rectangle
        dwg.add(dwg.rect(
            insert=(x_pos, current_y),
            size=(node_width, current_node_height),
            fill=fill_color,
            stroke=border_color,
            rx=5, ry=5 # Rounded corners for aesthetics
        ))

        # --- Text Rendering inside Node ---
        # Create an SVG text element. Text will be added as <tspan> elements for multi-line.
        text_element = dwg.text("", # Initial text is empty
                                insert=(x_pos + node_width / 2, 0), # X is centered, Y will be set by first tspan
                                stroke='none',
                                fill=text_color,
                                font_size=f'{line_height_px * 0.8}px', # Font size relative to line height
                                font_family='Arial',
                                text_anchor='middle') # Horizontal centering

        # Calculate vertical starting point for the block of text to center it within the node
        total_text_block_height = num_lines * line_height_px
        text_start_y = current_y + (current_node_height - total_text_block_height) / 2 + (line_height_px * 0.7) # Adjusted for better baseline alignment

        # Add each line of text as a <tspan>
        for line_idx, line_text_content in enumerate(lines):
            tspan = dwg.tspan(line_text_content, x=[x_pos + node_width / 2]) # x must be a list for tspan
            if line_idx == 0:
                tspan.attribs['y'] = text_start_y # Set absolute Y for the first line
            else:
                tspan.attribs['dy'] = f"{line_height_px}px" # Relative Y (delta Y) for subsequent lines
            text_element.add(tspan)
        dwg.add(text_element)
        # --- End Text Rendering ---

        # Update current_y for the next node and track maximum x extent
        current_y += current_node_height + margin
        if x_pos + node_width > max_x_pos:
            max_x_pos = x_pos + node_width
    # --- End First Pass ---

    # --- Second Pass: Connection Drawing ---
    # Iterate through the stored nodes_map to draw lines between them.
    for step_id, node_info in nodes_map.items():
        source_step_data = node_info['step_data'] # Original JSON data for this step

        # Handle 'previous_decision' loop: skip drawing an outgoing line from this node.
        # The connection *to* this node (e.g. from a "Yes" option) will be drawn by the source decision node.
        if source_step_data.get("nextStepID") and source_step_data["nextStepID"] == "previous_decision":
            # Optional: print(f"Info: Step '{step_id}' leads to 'previous_decision', its outgoing line is implicitly handled.")
            continue

        # --- Action Node Connections ---
        if node_info['type'] == 'action' and source_step_data.get('nextStepID'):
            target_id = source_step_data['nextStepID']
            if target_id in nodes_map: # Check if target node exists
                # Calculate start and end points for the line
                x1, y1, x2, y2 = get_connection_points((step_id, node_info), (target_id, nodes_map[target_id]), nodes_map)
                # Add line with arrowhead
                dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=line_color, stroke_width=2, marker_end=arrowhead.get_funciri()))
                # Update SVG dimensions if line extends them
                if x1 > max_x_pos: max_x_pos = x1
                if x2 > max_x_pos: max_x_pos = x2
                if y1 > current_y: current_y = y1
                if y2 > current_y: current_y = y2
            elif target_id: # Target ID specified but not found
                print(f"Warning: Step '{step_id}' (action) refers to nextStepID '{target_id}' which does not exist. Connection skipped.")

        # --- Decision Node Connections ---
        elif node_info['type'] == 'decision' and source_step_data.get('options'):
            for option_idx, option in enumerate(source_step_data['options']):
                target_id = option.get('nextStepID')
                if target_id and target_id in nodes_map: # Check if target node for this option exists
                    x1, y1, x2, y2 = get_connection_points((step_id, node_info), (target_id, nodes_map[target_id]), nodes_map)

                    dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=line_color, stroke_width=2, marker_end=arrowhead.get_funciri()))

                    # Add decision text (e.g., "Yes", "No") near the start/midpoint of the line
                    # Basic text placement, could be improved with path-based text or more complex calculations.
                    line_text_x = (x1 + x2) / 2 + 5
                    line_text_y = (y1 + y2) / 2 - 5
                    dwg.add(dwg.text(option.get('decisionText', ''), insert=(line_text_x, line_text_y),
                                     fill=text_color, font_size='12px', font_family='Arial'))

                    # Update SVG dimensions if line or text extends them
                    if x1 > max_x_pos: max_x_pos = x1
                    if x2 > max_x_pos: max_x_pos = x2
                    if line_text_x > max_x_pos: max_x_pos = line_text_x
                    if y1 > current_y: current_y = y1
                    if y2 > current_y: current_y = y2
                    if line_text_y > current_y: current_y = line_text_y
                elif target_id: # Target ID specified but not found
                    print(f"Warning: Step '{step_id}' (decision, option '{option.get('decisionText', option_idx)}') " +
                          f"refers to nextStepID '{target_id}' which does not exist. Connection skipped.")
                # No 'else' needed here for missing target_id in option, as we just skip that option's line.
    # --- End Second Pass ---

    # Dynamically set the SVG drawing's final width and height based on content.
    dwg.attribs['width'] = f"{max_x_pos + margin}px"
    dwg.attribs['height'] = f"{current_y + margin}px" # Add margin to bottom as well for padding

    return dwg.tostring() # Return SVG as an XML string
