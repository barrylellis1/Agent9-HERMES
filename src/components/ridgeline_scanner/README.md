# Ridgeline Scanner Component

This is a custom Streamlit component that renders an animated "Ridgeline" (Joyplot) visualization using React, Visx, and Framer Motion.

## How it Works
This component is a "Black Box" visualization. You feed it Python data, and it handles all the complex rendering and animation internally.

## Usage (Python)

```python
from src.components.ridgeline_scanner import ridgeline_scanner

# Define your categories (rows)
categories = ["Region A", "Region B", "Region C"]

# Define your data (lists of values for each category)
# Each list represents the distribution of values for that row
data = [
    [0.1, 0.2, 0.5, ...],  # Region A data
    [-0.5, -0.2, 0.1, ...], # Region B data
    [0.0, 0.0, 0.1, ...]   # Region C data
]

# Render the chart
ridgeline_scanner(
    data=data,
    categories=categories,
    title="Margin Distribution Scanner"
)
```

## Development

The frontend code lives in `frontend/`. It is a React application built with Vite.

### Prerequisites
- Node.js (v18+)
- npm

### Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev` (to start the dev server for hot-reloading)

### Building for Production
1. `cd frontend`
2. `npm run build`
3. Set `_RELEASE = True` in `__init__.py`
