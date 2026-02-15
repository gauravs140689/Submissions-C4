# AI Financial Coach Pro 💎

AI Financial Coach Pro is a powerful personal finance application built with Streamlit. It helps you track expenses, analyze your financial health, and receive personalized AI-driven advice to improve your financial well-being.

## Features

### 📊 **Interactive Dashboard**
- **Financial Health Score**: Get a comprehensive score (0-100) based on your income, expenses, savings, and debt.
- **KPI Cards**: Monitor key metrics like Net Balance, Savings Rate, Total Expenses, and Financial Health at a glance.
- **Visualizations**:
    - **Gauge Chart**: Visual representation of your financial health.
    - **Expense Breakdown**: Interactive pie chart showing spending by category.
    - **Cash Flow Forecast**: 5-year projection of your financial future based on current trends.

### 📝 **Smart Data Input**
- **Manual Income Entry**: Easily input your monthly income.
- **PDF Bank Statement Upload**: Upload your bank statement (PDF format) to automatically parse and categorize transactions.
- **Expense Tracker**: Manually add daily expenses with categories (Food, Transport, Rent, etc.) and descriptions.

### 🤖 **AI-Powered Insights**
Receive personalized financial advice from specialized AI agents:
- **Debt Analyzer**: Strategies to manage and reduce debt efficiently.
- **Savings Strategy**: Tips to optimize your savings based on your income and expenses.
- **Investment Agent**: Tailored investment advice considering your risk profile.
- **Budget Advisor**: Smart budgeting recommendations to help you stay on track.

### ⚙️ **Customization**
- **Dark/Light Mode**: Toggle between themes for a comfortable viewing experience.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd ai_financial_coach
    ```

2.  **Create a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `streamlit`, `pandas`, `plotly`, and `pdfplumber` are installed.*

## Usage

1.  **Run the application**:
    ```bash
    streamlit run app.py
    ```

2.  **Navigate the App**:
    -   **Dashboard**: View your financial overview, upload bank statements, and see AI insights.
    -   **Expense Tracker**: Add individual expenses manually.

## Technologies Used

-   **Frontend**: Streamlit
-   **Data Manipulation**: Pandas
-   **Visualization**: Plotly
-   **PDF Parsing**: pdfplumber
-   **AI/LLM Integration**: LangChain, OpenAI GPT-4o-mini (via OpenRouter)
