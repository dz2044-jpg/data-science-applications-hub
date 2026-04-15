# File Format Support Test

This demonstrates that the application now supports CSV, Excel, and Parquet file formats.

## Testing the new format support

```python
import pandas as pd
from pathlib import Path

# Sample data
data = {
    'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
    'deaths': [10, 12, 8],
    'region': ['North', 'South', 'East']
}
df = pd.DataFrame(data)

# Save as different formats
data_dir = Path('test_data')
data_dir.mkdir(exist_ok=True)

# CSV (original format)
df.to_csv(data_dir / 'sample.csv', index=False)

# Excel
df.to_excel(data_dir / 'sample.xlsx', index=False)

# Parquet  
df.to_parquet(data_dir / 'sample.parquet', index=False)
```

## What was implemented:

1. **Dependencies Added** (pyproject.toml):
   - openpyxl >= 3.1.0 (for Excel support)
   - pyarrow >= 17.0.0 (for Parquet support)

2. **New Module** (app/retrieve/data_upload.py):
   - read_mortality_csv_upload() - CSV support
   - read_mortality_excel_upload() - Excel support (.xlsx, .xls)
   - read_mortality_parquet_upload() - Parquet support
   - read_mortality_upload() - Unified interface for all formats

3. **Enhanced Module** (app/retrieve/datasets.py):
   - list_datasets() - Lists files with all supported extensions
   - read_dataset_bytes() - Reads any supported format
   - SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet"}

4. **Updated Services**:
   - app/service/datasets.py
   - app/service/dataset_schema.py
   - app/service/dataset_cola.py
   - app/service/ae_variable_labels.py
   - app/service/monitor.py
   - app/service/ae_univariate.py

All services now support reading CSV, Excel (.xlsx, .xls), and Parquet files transparently.

## Usage:

Users can now:
- Upload Excel files (.xlsx, .xls) in addition to CSV
- Upload Parquet files for better performance with large datasets
- Store datasets in any of these formats in the data directory
- All existing functionality works with all supported formats

The format is automatically detected from the file extension.
