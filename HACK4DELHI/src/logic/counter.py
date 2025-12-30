class VehicleCounter:
    def __init__(self, max_capacity):
        """
        max_capacity: maximum allowed parking capacity
        """
        self.count = 0
        self.max_capacity = max_capacity

    def process_event(self, event):
        """
        event: 'ENTRY', 'EXIT', or None
        Updates count based on event
        Returns current count
        """

        if event == "ENTRY":
            self.count += 1
            print(f"🟢 ENTRY | Current Count = {self.count}")

            if self.count > self.max_capacity:
                print("🚨 ALERT: Parking capacity exceeded!")

        elif event == "EXIT":
            # Prevent negative count
            self.count = max(0, self.count - 1)
            print(f"🔵 EXIT  | Current Count = {self.count}")

        return self.count

    def get_count(self):
        return self.count