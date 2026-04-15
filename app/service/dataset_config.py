from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from app.models.dataset_config import (
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
)
from app.service.storage import (
    get_config_file_dir,
    get_configs_file,
    get_dataset_file_path,
    normalize_stored_file_path,
)


def save_uploaded_file(config_id: str, file_content: BinaryIO, filename: str) -> Path:
    """Save an uploaded file for a configuration."""
    config_dir = get_config_file_dir(config_id, create=True)
    file_path = config_dir / filename
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file_content, f)
    
    return file_path


def get_config_file_path(config_id: str) -> Path | None:
    """Get the file path for a configuration's saved file."""
    configs = _load_configs()
    config = next((c for c in configs if c.id == config_id), None)
    
    if not config:
        return None
    
    file_path = get_dataset_file_path(config_id, config.file_path)
    
    if file_path is not None and file_path.exists():
        return file_path
    return None


def get_dataset_config_with_file(config_id: str) -> tuple[ApiDatasetConfig, Path]:
    """Get a saved configuration and its stored file path."""
    config = get_dataset_config(config_id)
    if config is None:
        raise ValueError(f"Dataset config '{config_id}' not found")

    file_path = get_config_file_path(config_id)
    if file_path is None:
        raise ValueError(f"File for config '{config_id}' not found")

    return config, file_path


def _load_configs() -> list[ApiDatasetConfig]:
    """Load all dataset configurations from disk."""
    configs_file = get_configs_file()
    if not configs_file.exists():
        return []
    
    try:
        with open(configs_file, encoding="utf-8") as f:
            data = json.load(f)
        
        configs = []
        for item in data:
            # Parse datetime string back to datetime object
            item["created_date"] = datetime.fromisoformat(item["created_date"])
            configs.append(ApiDatasetConfig(**item))
        return configs
    except Exception:
        return []


def _save_configs(configs: list[ApiDatasetConfig]) -> None:
    """Save all dataset configurations to disk."""
    configs_file = get_configs_file()
    
    # Convert to dict for JSON serialization
    data = []
    for config in configs:
        config_dict = config.model_dump()
        # Convert datetime to ISO format string
        config_dict["created_date"] = config.created_date.isoformat()
        data.append(config_dict)
    
    with open(configs_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_dataset_configs() -> ApiListDatasetConfigsResults:
    """List all saved dataset configurations."""
    configs = _load_configs()
    # Sort by created_date descending (newest first)
    configs.sort(key=lambda c: c.created_date, reverse=True)
    return ApiListDatasetConfigsResults(configs=configs)


def create_dataset_config(request: ApiCreateDatasetConfigRequest) -> ApiDatasetConfig:
    """Create a new dataset configuration."""
    configs = _load_configs()
    
    # Generate unique ID
    config_id = str(uuid.uuid4())
    stored_file_path, _ = normalize_stored_file_path(config_id, request.file_path)
    
    # Create new config
    new_config = ApiDatasetConfig(
        id=config_id,
        dataset_name=request.dataset_name,
        performance_type=request.performance_type,
        file_path=stored_file_path,
        module_id=request.module_id,
        module_config=request.module_config,
        created_date=datetime.now(),
    )
    
    # Add to list and save
    configs.append(new_config)
    _save_configs(configs)
    
    return new_config


def get_dataset_config(config_id: str) -> ApiDatasetConfig | None:
    """Get a specific dataset configuration by ID."""
    configs = _load_configs()
    for config in configs:
        if config.id == config_id:
            return config
    return None


def delete_dataset_config(config_id: str) -> bool:
    """Delete a dataset configuration by ID. Returns True if deleted, False if not found."""
    configs = _load_configs()
    original_count = len(configs)
    configs = [c for c in configs if c.id != config_id]
    
    if len(configs) < original_count:
        _save_configs(configs)
        
        # Also delete the associated file directory
        try:
            config_dir = get_config_file_dir(config_id, create=False)
            if config_dir.exists():
                shutil.rmtree(config_dir)
        except Exception:
            pass  # Continue even if file deletion fails
        
        return True
    return False
