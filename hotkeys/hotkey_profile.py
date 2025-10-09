import json
import os

class HotkeyProfile:
    """Represents a single hotkey profile with action-to-key mappings."""
    
    def __init__(self, name: str, bindings: dict[str, str]):
        """
        :param name: Profile name (e.g., "default", "hotkey1").
        :param bindings: Dict of action_name: key_sequence_str (e.g., {"toggle_grid": "G"}).
        """
        self.name = name
        self.bindings = bindings  # e.g., {"toggle_grid": "G", "add_sphere": "Ctrl+S"}

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {"name": self.name, "bindings": self.bindings}

    @classmethod
    def from_dict(cls, data: dict) -> 'HotkeyProfile':
        """Create from dict (loaded from JSON)."""
        return cls(data["name"], data["bindings"])

    def save_to_json(self, path: str) -> None:
        """Save profile to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_from_json(cls, path: str) -> 'HotkeyProfile':
        """Load profile from JSON file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Profile not found: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)