# 🔍 Intelligent Code Reviewer & Explainer

[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM_API-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> AI-powered code analysis platform that provides comprehensive bug detection, security auditing, code explanations, and optimization suggestions — powered by NVIDIA NIM and LLaMA 3.3 70B.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Quality Scoring** | Overall code quality score (0–100) with complexity and maintainability grades |
| 🐛 **Bug Detection** | Critical, major, and minor bug identification with fix suggestions |
| 🔒 **Security Audit** | Detects hardcoded secrets, SQL injection, XSS, unsafe file ops, and more |
| 📖 **Code Explanation** | Plain-English function-by-function breakdown and workflow analysis |
| ⚡ **Optimization** | Performance, readability, refactoring, and scalability suggestions |
| ✨ **Refactored Code** | Complete optimized version of your source code |
| 📄 **Report Generation** | Downloadable reports in Markdown and PDF formats |

## 🏗️ Architecture

```
project-root/
├── app.py                    # Main Streamlit entry point
├── assets/
│   ├── styles.css            # Premium dark theme CSS
│   └── logo.png              # App logo
├── components/
│   ├── upload_section.py     # File upload + code preview
│   ├── metrics_cards.py      # Glassmorphism metric cards
│   ├── analysis_tabs.py      # 7-tab results display
│   └── report_download.py    # PDF/Markdown download buttons
├── services/
│   ├── llm_service.py        # NVIDIA NIM API client
│   ├── code_analyzer.py      # Analysis orchestration
│   └── report_generator.py   # Report generation (MD + PDF)
├── prompts/
│   └── review_prompt.py      # Structured prompts + JSON schema
├── utils/
│   ├── file_reader.py        # File validation + reading
│   ├── syntax_detector.py    # Language auto-detection
│   └── markdown_parser.py    # Rendering helpers
├── .env.example              # Environment template
├── .streamlit/config.toml    # Streamlit configuration
└── requirements.txt          # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- NVIDIA API Key (free) from [build.nvidia.com](https://build.nvidia.com)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd "Task 6"

# 2. Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

### Run Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NVIDIA_API_KEY` | *required* | Your NVIDIA NIM API key |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | API endpoint |
| `NVIDIA_MODEL` | `meta/llama-3.3-70b-instruct` | Model identifier |
| `LLM_MAX_TOKENS` | `4096` | Max output tokens |
| `LLM_TIMEOUT_SECONDS` | `300` | Read timeout (seconds) |
| `LLM_TEMPERATURE` | `0.1` | Generation temperature |

### Supported Languages

| Language | Extension |
|----------|-----------|
| Python | `.py` |
| JavaScript | `.js` |
| TypeScript | `.ts` |
| Java | `.java` |
| C | `.c` |
| C++ | `.cpp` |

## ☁️ Deployment (Streamlit Cloud)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set the main file path to `app.py`
5. Add your `NVIDIA_API_KEY` in **Settings → Secrets**:

```toml
NVIDIA_API_KEY = "nvapi-your-key-here"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"
```

## 🛡️ Security

- API keys are never exposed in source code
- File uploads are validated (type, size, encoding)
- LLM outputs are sanitized before rendering
- Anti-prompt-injection safeguards in system prompts
- Environment variables managed via `.env` (gitignored)

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit + Custom CSS |
| **Backend** | Python 3.11+ |
| **AI Model** | Meta LLaMA 3.3 70B via NVIDIA NIM |
| **API Client** | OpenAI Python SDK (compatible) |
| **PDF Generation** | fpdf2 |
| **Retry Logic** | tenacity |
| **Config** | python-dotenv |

---

*Built with ❤️ as a production-grade AI developer tool.*
