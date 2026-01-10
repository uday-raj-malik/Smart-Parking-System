class LineCrossing:
    def __init__(self, line_y, margin=15):
        self.line_y = line_y
        self.margin = margin
        self.states = {}  # entity_id -> "ABOVE" | "BELOW"

    def check(self, entity_id, cy):
        current_state = "ABOVE" if cy < self.line_y else "BELOW"

        if entity_id not in self.states:
            self.states[entity_id] = current_state
            return None

        prev_state = self.states[entity_id]

        if abs(cy - self.line_y) < self.margin:
            return None

        if prev_state == "ABOVE" and current_state == "BELOW":
            self.states[entity_id] = current_state
            return "ENTRY"

        if prev_state == "BELOW" and current_state == "ABOVE":
            self.states[entity_id] = current_state
            return "EXIT"

        return None
