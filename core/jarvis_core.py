class JarvisCore:
    def __init__(self):
        self.name = "JARVIS"
        self.status = "ONLINE"

    def start(self):
        print(f"{self.name} core started.")
        print(f"Status: {self.status}")