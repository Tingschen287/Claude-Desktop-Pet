# src/skin_registry.py
# Skin registry for Claude Desktop Pet - discovers and loads skin modules.

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


def load_module_from_path(module_name: str, file_path: Path | str) -> Any:
    """Load a Python module from a file path.

    Args:
        module_name: Unique name for the module in sys.modules
        file_path: Path to the Python file to load

    Returns:
        The loaded module

    Raises:
        ImportError: If the module cannot be loaded
    """
    file_path = Path(file_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class SkinModule:
    """Wrapper for a skin module with validation."""

    REQUIRED_ATTRS = ["META", "ROWS", "COLS", "FRAMES", "FRAME_INTERVALS", "STATE_MOTION"]
    REQUIRED_STATES = ["unconfigured", "idle", "thinking", "reading", "writing", "executing", "waiting"]

    def __init__(self, module: Any, path: str):
        self._module = module
        self._path = path
        self._validate()

    def _validate(self) -> None:
        """Validate that the module has all required attributes."""
        for attr in self.REQUIRED_ATTRS:
            if not hasattr(self._module, attr):
                raise ValueError(f"Skin module missing required attribute: {attr}")

        # Validate META
        meta = self._module.META
        if not isinstance(meta, dict):
            raise ValueError("META must be a dictionary")
        if "name" not in meta or "id" not in meta:
            raise ValueError("META must contain 'name' and 'id' keys")

        # Validate FRAMES has all required states
        frames = self._module.FRAMES
        for state in self.REQUIRED_STATES:
            if state not in frames:
                raise ValueError(f"FRAMES missing required state: {state}")
            if not frames[state]:
                raise ValueError(f"FRAMES[{state}] is empty")

    @property
    def id(self) -> str:
        return self._module.META["id"]

    @property
    def name(self) -> str:
        return self._module.META["name"]

    @property
    def rows(self) -> int:
        return self._module.ROWS

    @property
    def cols(self) -> int:
        return self._module.COLS

    @property
    def frames(self) -> dict:
        return self._module.FRAMES

    @property
    def frame_intervals(self) -> dict:
        return self._module.FRAME_INTERVALS

    @property
    def state_motion(self) -> dict:
        return self._module.STATE_MOTION

    def __repr__(self) -> str:
        return f"SkinModule(id={self.id!r}, name={self.name!r})"


class SkinRegistry:
    """Registry for discovering and loading skin modules."""

    def __init__(self):
        self._skins: dict[str, SkinModule] = {}
        self._scan_skins()

    def _scan_skins(self) -> None:
        """Scan built-in and user skin directories."""
        # Scan built-in skins (assets/skins/)
        builtin_dir = Path(__file__).parent.parent / "assets" / "skins"
        if builtin_dir.exists():
            self._scan_directory(builtin_dir, is_builtin=True)

        # Scan user skins (~/.claude/pet-skins/)
        user_dir = Path.home() / ".claude" / "pet-skins"
        if user_dir.exists():
            self._scan_directory(user_dir, is_builtin=False)

    def _scan_directory(self, directory: Path, is_builtin: bool) -> None:
        """Scan a directory for skin modules."""
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # Check for Python skin module
                skin_path = item / "__init__.py"
                if skin_path.exists():
                    try:
                        skin = self._load_skin(item)
                        if skin:
                            self._skins[skin.id] = skin
                    except Exception as e:
                        print(f"Warning: Failed to load skin from {item}: {e}", file=sys.stderr)
                # Check for SVG-based skin (user skins only)
                elif not is_builtin:
                    svg_skin = self._try_load_svg_skin(item)
                    if svg_skin:
                        self._skins[svg_skin.id] = svg_skin

    def _try_load_svg_skin(self, skin_dir: Path) -> Optional[SkinModule]:
        """Try to load an SVG-based skin."""
        config_path = skin_dir / "config.json"
        svg_files = list(skin_dir.glob("*.svg"))

        if not config_path.exists() or not svg_files:
            return None

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))

            # Find base.svg or use first SVG file
            svg_path = skin_dir / "base.svg"
            if not svg_path.exists():
                svg_path = svg_files[0]

            # Generate skin module from SVG
            generated_dir = skin_dir / "generated"
            generated_dir.mkdir(parents=True, exist_ok=True)

            # Use svg2skin module to generate frames
            from svg2skin import create_skin_from_svg
            if create_skin_from_svg(str(svg_path), config, generated_dir):
                return self._load_skin(generated_dir)
        except Exception as e:
            print(f"Warning: Failed to load SVG skin from {skin_dir}: {e}", file=sys.stderr)
            return None

    def _load_skin(self, skin_dir: Path) -> Optional[SkinModule]:
        """Load a skin module from a directory."""
        skin_id = skin_dir.name
        init_path = skin_dir / "__init__.py"
        module_name = f"pet_skin_{skin_id}"

        try:
            module = load_module_from_path(module_name, init_path)
            return SkinModule(module, str(skin_dir))
        except ImportError:
            return None

    def get_skin(self, skin_id: str) -> SkinModule:
        """Get a skin by ID. Returns default skin if not found."""
        if skin_id in self._skins:
            return self._skins[skin_id]
        # Fallback to default
        if "default" in self._skins:
            return self._skins["default"]
        raise RuntimeError("No default skin available")

    def list_skins(self) -> list[SkinModule]:
        """List all available skins."""
        return list(self._skins.values())

    def get_skin_ids(self) -> list[str]:
        """Get list of skin IDs."""
        return list(self._skins.keys())


# Global registry instance
_registry: Optional[SkinRegistry] = None


def get_registry() -> SkinRegistry:
    """Get the global skin registry."""
    global _registry
    if _registry is None:
        _registry = SkinRegistry()
    return _registry
