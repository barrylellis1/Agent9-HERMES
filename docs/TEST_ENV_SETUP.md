# Agent9-APOLLO Test Environment Setup

This guide describes how to set up and run the Agent9-APOLLO test environment for local development, integration, and end-to-end testing.

---

## 1. Prerequisites
- **Python:** 3.11.x (recommended)
- **pip:** Latest version
- **Virtual Environment:** Strongly recommended (venv or conda)
- **Node.js:** (Optional, if using frontend tools)
- **DuckDB:** No separate install needed; Python package is used

---

## 2. Clone the Repository
```sh
git clone <YOUR_AGENT9_REPO_URL>
cd Agent9-APOLLO
```

---

## 3. Create and Activate Virtual Environment
```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

---

## 4. Install Python Dependencies
```sh
pip install --upgrade pip
pip install -r requirements.txt
```
_If you use `pyproject.toml`/`poetry`, adjust accordingly._

---

## 5. Environment Variables
Create a `.env` file in the project root (if not present) and set:
```
OPENAI_API_KEY=<your-openai-key>
AGENT9_DUCKDB_PATH=C:/Agent9Data/agent9-apollo.duckdb  # or your preferred path
# Add other required variables as needed
```

---

## 6. Prepare Test Data
- Ensure all required CSVs are present in the directories referenced by your YAML data product contracts and the data product registry.
- Example: `src/registry_references/data_product_registry/data_products/` for YAML contracts.
- Example: `C:/Agent9Data/csv/` for raw CSVs (see contract and registry for exact paths).

---

## 7. Start Backend API Server
```sh
uvicorn src.api.main:app --reload --port 8000
```
- The API will be available at [http://localhost:8000](http://localhost:8000)

---

## 8. Start Streamlit UI (NLP-to-SQL Test UI)
```sh
streamlit run nlp_sql_test_ui.py --server.port 8501
```
- The UI will be available at [http://localhost:8501](http://localhost:8501)

---

## 9. Running Tests
- (Add instructions for pytest or other test runners if applicable)

---

## 10. Troubleshooting
- **ModuleNotFoundError:** Ensure you are in the correct virtual environment and all dependencies are installed.
- **DuckDB/CSV errors:** Check that all CSV/data paths match those referenced in your contracts and registry.
- **API Key errors:** Ensure your `.env` file is present and loaded.
- **Debug logs:** Check API and UI logs for detailed debug output.

---

## 11. Updating Dependencies
```sh
pip freeze > requirements.txt
```

---

## 12. Additional Notes
- Follow the Agent9 code and config sync rules for agent/contract changes.
- See `docs/Agent9_Agent_Design_Standards.md` for agent standards and compliance.
- For more details, check the main `README.md` or ask Cascade for help!
