export type ApiSeriesFormat = 'number' | 'percent';

export interface ApiChartColumn {
    name: string;
    format: ApiSeriesFormat;
}

export type ApiChartCell = number | null;

export interface ApiChartTable {
    columns: ApiChartColumn[];
    rows: ApiChartCell[][];
}

