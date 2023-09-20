from pathlib import Path


class PathResolution:
    def __init__(self):
        self.root = Path(__file__).parent.parent.resolve()
        self.models = self.root / "models"
        self.common = self.root / "common"
        self.environments = self.root / "environments"