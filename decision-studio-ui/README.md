# Agent9 Decision Studio UI

This is the "Consumer Grade" frontend for the Agent9 Decision Studio.

## The Stack
- **Framework:** React + Vite
- **Styling:** Tailwind CSS
- **Animation:** Framer Motion
- **Visualization:** Visx (by Airbnb)

## Key Features
- **Ridgeline Scanner:** Visualizes KPI distribution shapes over time (the "Time Machine" effect).
- **Dark Mode:** Executive-style dashboard aesthetic.

## Setup & Run

1. Open a terminal.
2. Navigate to this folder:
   ```bash
   cd decision-studio-ui
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start the dev server:
   ```bash
   npm run dev
   ```
5. Open the URL shown (usually `http://localhost:5173`).

## Connecting to Backend
This UI connects to the Python API running at `http://localhost:8000`. Ensure you have started the Agent9 backend servers separately.
