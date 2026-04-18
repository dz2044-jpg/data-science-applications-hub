"""
Quick test to verify Excel and Parquet file format support.
Run this to create sample files in different formats and verify they can be read.
"""
import pandas as pd
from pathlib import Path
import tempfile
from app.retrieve.datasets import list_datasets, read_dataset_bytes
from app.retrieve.data_upload import (
    read_mortality_csv_upload,
    read_mortality_excel_upload,
    read_mortality_parquet_upload,
    read_mortality_upload,
)

def test_file_formats():
    """Create sample files in different formats and verify they can be read."""
    
    # Sample data
    data = {
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'deaths': [10, 12, 8],
        'region': ['North', 'South', 'East']
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create files in different formats
        csv_file = data_dir / 'sample.csv'
        excel_file = data_dir / 'sample.xlsx'
        parquet_file = data_dir / 'sample.parquet'
        
        df.to_csv(csv_file, index=False)
        df.to_excel(excel_file, index=False, engine='openpyxl')
        df.to_parquet(parquet_file, index=False, engine='pyarrow')
        
        # Test list_datasets
        datasets = list_datasets(data_dir=data_dir)
        print(f"✓ Found {len(datasets)} datasets: {datasets}")
        assert len(datasets) == 3
        assert 'sample.csv' in datasets
        assert 'sample.xlsx' in datasets
        assert 'sample.parquet' in datasets
        
        # Test read_dataset_bytes for each format
        for filename in datasets:
            file_bytes = read_dataset_bytes(data_dir=data_dir, dataset_name=filename)
            print(f"✓ Read {len(file_bytes)} bytes from {filename}")
            assert len(file_bytes) > 0
        
        # Test mortality upload functions
        csv_bytes = csv_file.read_bytes()
        df_csv = read_mortality_csv_upload(
            csv_bytes=csv_bytes,
            date_column='date',
            value_column='deaths',
            group_column='region',
            date_format=None
        )
        print(f"✓ CSV upload: {len(df_csv)} rows")
        assert len(df_csv) == 3
        
        excel_bytes = excel_file.read_bytes()
        df_excel = read_mortality_excel_upload(
            excel_bytes=excel_bytes,
            date_column='date',
            value_column='deaths',
            group_column='region',
            date_format=None
        )
        print(f"✓ Excel upload: {len(df_excel)} rows")
        assert len(df_excel) == 3
        
        parquet_bytes = parquet_file.read_bytes()
        df_parquet = read_mortality_parquet_upload(
            parquet_bytes=parquet_bytes,
            date_column='date',
            value_column='deaths',
            group_column='region',
            date_format=None
        )
        print(f"✓ Parquet upload: {len(df_parquet)} rows")
        assert len(df_parquet) == 3
        
        # Test unified interface
        for file_format, file_bytes in [('csv', csv_bytes), ('excel', excel_bytes), ('parquet', parquet_bytes)]:
            df_unified = read_mortality_upload(
                file_bytes=file_bytes,
                file_format=file_format,
                date_column='date',
                value_column='deaths',
                group_column='region',
                date_format=None
            )
            print(f"✓ Unified interface ({file_format}): {len(df_unified)} rows")
            assert len(df_unified) == 3
        
        print("\n✅ All file format tests passed!")

if __name__ == '__main__':
    test_file_formats()
