class LineCrossing:
    def __init__(self, line_y):
        self.line_y = line_y
        # Stores the last known Y position for each vehicle ID
        # Format: { vehicle_id : y_position }
        self.previous_positions = {}

    def check(self, id, current_y):
        # If we haven't seen this car before, just store its position
        if id not in self.previous_positions:
            self.previous_positions[id] = current_y
            return None

        prev_y = self.previous_positions[id]

        # Update the position for next time
        self.previous_positions[id] = current_y

        # --- LOGIC FOR CROSSING ---

        # Case 1: Moving DOWN (Top to Bottom)
        # Previous Y was above line, Current Y is below line
        if prev_y < self.line_y and current_y >= self.line_y:
            return "ENTRY"  # Assuming entering is moving down

        # Case 2: Moving UP (Bottom to Top)
        # Previous Y was below line, Current Y is above line
        if prev_y > self.line_y and current_y <= self.line_y:
            return "EXIT"  # Assuming exiting is moving up

        return None