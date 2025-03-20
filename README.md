# AgentAnalyzer

AgentAnalyzer is a Python-based application that utilizes OpenAI's GPT-4 model to transform raw CSV data into structured Excel files based on user-defined templates. By leveraging Streamlit for the user interface, it offers an intuitive platform for users to upload their datasets and receive AI-processed outputs tailored to specific formats.

## Features

- **AI-Powered Data Transformation**: Harnesses GPT-4 to interpret and restructure raw data according to predefined templates.
- **Interactive Web Interface**: Employs Streamlit to provide a seamless user experience for data uploads and downloads.
- **Customizable Templates**: Supports user-defined Excel templates to ensure outputs meet specific requirements.
- **Error Handling & Logging**: Incorporates robust error detection and logging mechanisms to ensure data integrity and provide user feedback.

## Setup and Installation

### Prerequisites
- **Python 3.8 or higher**
- **OpenAI API Key**: Obtain an API key from OpenAI to access GPT-4 functionalities.

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/nisthaKumar/AgentAnalyzer.git
   cd AgentAnalyzer
   ```
2. Create a virtual environment
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
     ```
     pip install -r requirements.txt
     ```
4. Set up OpenAI API Key:

      - Export the OpenAI API key as an environment variable:

        ```
        export OPENAI_API_KEY="your_openai_api_key"
        ```
      - Alternatively, create a .env file in the project root and add:

        ```
        OPENAI_API_KEY=your_openai_api_key
        ```
## Project Structure
```
AgentAnalyzer/
├── .devcontainer/          # Development container configurations
├── agents/                 # Modules handling data processing
│   ├── ai_mapping.py       # AI-driven data mapping
│   ├── data_mapping.py     # Data preprocessing and mapping logic
│   ├── extract_csv.py      # CSV extraction utilities
│   ├── merge_csv.py        # CSV merging utilities
│   ├── merge_strategy.py   # Strategies for data merging
│   ├── populate_template.py# Populates templates with AI-processed data
│   └── template_context.py # Contextual data handling for templates
├── .gitignore              # Git ignore file
├── README.md               # Project documentation
├── main.py                 # Streamlit application entry point
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (e.g., API keys)
```


