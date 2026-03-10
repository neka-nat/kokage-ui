# Chart Demo

Interactive Chart.js demo with 6 chart types and live random chart generation.

## Features

- **6 chart types**: Line, Bar, Pie, Doughnut, Radar, Scatter
- **Typed data models**: `Dataset`, `ChartData`, `ChartOptions` for IDE completion
- **Live update**: htmx fragment generates random charts on button click
- **Theme switching**: DarkModeToggle + ThemeSwitcher

## Run

```bash
uv run uvicorn examples.chart_demo:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Source

```python
--8<-- "examples/chart_demo.py"
```
