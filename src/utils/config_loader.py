"""Configuration loading and validation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """Loads and manages configuration from YAML files with environment variable support."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration loader.

        Args:
            config_dir: Directory containing configuration files. Defaults to ./config/
        """
        if config_dir is None:
            config_dir = Path.cwd() / "config"
        self.config_dir = Path(config_dir)
        load_dotenv()  # Load .env file if present

    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file with environment variable interpolation.

        Args:
            filename: Name of YAML file to load

        Returns:
            Parsed configuration dictionary
        """
        filepath = self.config_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, "r") as f:
            content = f.read()

        # Replace environment variables in the format ${VAR_NAME}
        content = self._interpolate_env_vars(content)

        try:
            config = yaml.safe_load(content)
            return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {filename}: {e}")

    def _interpolate_env_vars(self, content: str) -> str:
        """Replace ${VAR_NAME} with environment variable values.

        Args:
            content: YAML content string

        Returns:
            Content with environment variables replaced
        """
        import re

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            return os.environ.get(var_name, default_value)

        # Pattern matches ${VAR_NAME} or ${VAR_NAME:default}
        pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*?)(?::([^}]*))?\}"
        return re.sub(pattern, replace_var, content)

    def load_gateways_config(self) -> Dict[str, Any]:
        """Load gateway configurations.

        Returns:
            Gateway configuration dictionary
        """
        return self.load_yaml("gateways.yaml")

    def load_test_suites_config(self) -> Dict[str, Any]:
        """Load test suite configurations.

        Returns:
            Test suite configuration dictionary
        """
        return self.load_yaml("test_suites.yaml")

    def get_enabled_gateways(self) -> Dict[str, Dict[str, Any]]:
        """Get only enabled gateway configurations.

        Returns:
            Dictionary of enabled gateway configurations
        """
        config = self.load_gateways_config()
        gateways = config.get("gateways", {})
        return {name: cfg for name, cfg in gateways.items() if cfg.get("enabled", True)}

    def get_enabled_test_suites(self) -> Dict[str, Dict[str, Any]]:
        """Get only enabled test suite configurations.

        Returns:
            Dictionary of enabled test suite configurations
        """
        config = self.load_test_suites_config()
        test_suites = config.get("test_suites", {})
        return {name: cfg for name, cfg in test_suites.items() if cfg.get("enabled", True)}

    def validate_gateway_config(self, gateway_name: str, config: Dict[str, Any]) -> bool:
        """Validate gateway configuration has required fields.

        Args:
            gateway_name: Name of the gateway
            config: Gateway configuration

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        # Basic validation - can be extended per gateway type
        if not config.get("url") and not config.get("proxy_url"):
            raise ValueError(f"Gateway {gateway_name} must have 'url' or 'proxy_url'")

        return True
