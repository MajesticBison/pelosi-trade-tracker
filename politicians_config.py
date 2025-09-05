#!/usr/bin/env python3
"""
Politicians configuration system for the trade tracker.
Supports multiple politicians with individual settings.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class PoliticianStatus(Enum):
    """Status of politician tracking."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"

@dataclass
class PoliticianConfig:
    """Configuration for a single politician."""
    name: str
    full_name: str
    search_name: str  # Name as it appears in House Clerk search
    discord_webhook: str
    channel_name: str
    status: PoliticianStatus = PoliticianStatus.ACTIVE
    description: str = ""
    party: str = ""
    state: str = ""
    chamber: str = "House"  # House or Senate
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PoliticianConfig':
        """Create from dictionary."""
        data['status'] = PoliticianStatus(data['status'])
        return cls(**data)

class PoliticiansManager:
    """Manages politician configurations."""
    
    def __init__(self, config_file: str = "politicians.json"):
        self.config_file = config_file
        self.politicians: Dict[str, PoliticianConfig] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load politician configurations from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        self.politicians[name] = PoliticianConfig.from_dict(config_data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error loading politicians config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def save_config(self) -> None:
        """Save politician configurations to file."""
        data = {}
        for name, config in self.politicians.items():
            data[name] = config.to_dict()
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _create_default_config(self) -> None:
        """Create default configuration with Pelosi."""
        pelosi_config = PoliticianConfig(
            name="pelosi",
            full_name="Nancy Pelosi",
            search_name="Pelosi, Nancy",
            discord_webhook="",  # Will be filled from .env
            channel_name="#pelosi-trades",
            status=PoliticianStatus.ACTIVE,
            description="Speaker Emerita, California",
            party="Democratic",
            state="CA",
            chamber="House"
        )
        self.politicians["pelosi"] = pelosi_config
        self.save_config()
    
    def add_politician(self, config: PoliticianConfig) -> None:
        """Add a new politician configuration."""
        self.politicians[config.name] = config
        self.save_config()
    
    def remove_politician(self, name: str) -> bool:
        """Remove a politician configuration."""
        if name in self.politicians:
            del self.politicians[name]
            self.save_config()
            return True
        return False
    
    def get_politician(self, name: str) -> Optional[PoliticianConfig]:
        """Get politician configuration by name."""
        return self.politicians.get(name)
    
    def get_active_politicians(self) -> List[PoliticianConfig]:
        """Get all active politicians."""
        return [config for config in self.politicians.values() 
                if config.status == PoliticianStatus.ACTIVE]
    
    def get_politician_by_search_name(self, search_name: str) -> Optional[PoliticianConfig]:
        """Get politician by their search name."""
        for config in self.politicians.values():
            if config.search_name == search_name:
                return config
        return None
    
    def list_politicians(self) -> List[str]:
        """List all politician names."""
        return list(self.politicians.keys())
    
    def update_politician(self, name: str, **kwargs) -> bool:
        """Update politician configuration."""
        if name not in self.politicians:
            return False
        
        config = self.politicians[name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                if key == 'status' and isinstance(value, str):
                    value = PoliticianStatus(value)
                setattr(config, key, value)
        
        self.save_config()
        return True

def get_politician_config(name: str) -> Optional[PoliticianConfig]:
    """Convenience function to get a politician configuration."""
    manager = PoliticiansManager()
    return manager.get_politician(name)

def get_all_active_politicians() -> List[PoliticianConfig]:
    """Convenience function to get all active politicians."""
    manager = PoliticiansManager()
    return manager.get_active_politicians()

# Example politicians for easy setup
EXAMPLE_POLITICIANS = {
    "pelosi": PoliticianConfig(
        name="pelosi",
        full_name="Nancy Pelosi",
        search_name="Pelosi, Nancy",
        discord_webhook="",
        channel_name="#pelosi-trades",
        status=PoliticianStatus.ACTIVE,
        description="Speaker Emerita, California",
        party="Democratic",
        state="CA",
        chamber="House"
    ),
    "mccarthy": PoliticianConfig(
        name="mccarthy",
        full_name="Kevin McCarthy",
        search_name="McCarthy, Kevin",
        discord_webhook="",
        channel_name="#mccarthy-trades",
        status=PoliticianStatus.INACTIVE,
        description="Former Speaker, California",
        party="Republican",
        state="CA",
        chamber="House"
    ),
    "jeffries": PoliticianConfig(
        name="jeffries",
        full_name="Hakeem Jeffries",
        search_name="Jeffries, Hakeem",
        discord_webhook="",
        channel_name="#jeffries-trades",
        status=PoliticianStatus.INACTIVE,
        description="House Minority Leader, New York",
        party="Democratic",
        state="NY",
        chamber="House"
    ),
    "scott": PoliticianConfig(
        name="scott",
        full_name="Tim Scott",
        search_name="Scott, Tim",
        discord_webhook="",
        channel_name="#scott-trades",
        status=PoliticianStatus.INACTIVE,
        description="Senator, South Carolina",
        party="Republican",
        state="SC",
        chamber="Senate"
    )
}

if __name__ == "__main__":
    # Test the configuration system
    manager = PoliticiansManager()
    
    print("Current politicians:")
    for name, config in manager.politicians.items():
        print(f"  {name}: {config.full_name} ({config.status.value})")
    
    print(f"\nActive politicians: {len(manager.get_active_politicians())}")
