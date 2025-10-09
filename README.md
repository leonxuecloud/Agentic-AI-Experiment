# Agentic AI Experiment

Welcome to the Agentic AI Experiment repository!  
This space is dedicated to exploring the capabilities of Agentic AI—systems that exhibit autonomy, adaptability, and intelligent decision-making in complex environments.

The first project in this repository is the **MCP On-Call Assistant**, originally developed for the Caseware Hackathon 2025.

---

## About MCP On-Call Assistant

The MCP On-Call Assistant leverages Python and modern AI techniques to help automate incident response, repair workflow files, and provide intelligent knowledge base search. It’s designed to be modular, extensible, and easy to set up for experimentation and prototyping.

### Key Features

- 🤖 **AI-Powered Incident Response:** Smart recommendations for resolving incidents.
- 🎫 **JIRA Integration:** Seamless ticket management and tracking.
- 🔧 **CaseWare File Repair:** Automated detection and repair of corrupted CaseWare Working Papers archives.
- 🔍 **Knowledge Base Search:** AI-assisted search across documentation and resources.
- 📊 **WPLog Diagnostic Analysis:** Analyze CaseWare Working Papers log files with AI.

---

## Repository Structure

This repository may grow to include multiple Agentic AI experiments. Currently, it houses:

- `mcp-oncall-assistant/` — Source code and docs for the MCP On-Call Assistant

---

## Getting Started

### Requirements

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) (for dependency management, recommended)
- Visual Studio Code or another code editor
- (Optional) Git for version control

### Setup

1. **Clone this repository**
   ```bash
   git clone https://github.com/leonxuecloud/Agentic-AI-Experiment.git
   cd Agentic-AI-Experiment
   ```

2. **Install dependencies**
   Using [uv]:
   ```bash
   uv sync
   ```
   Or, using pip and venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Copy `.env.example` to `.env` and fill in the required configuration.
   ```bash
   cp .env.example .env
   ```

---

## Contributing

This repository welcomes experimentation and collaboration. Please feel free to ask for or open issues to talk about.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Agentic AI Experiment — Pioneering autonomy, intelligence, and adaptability in software agents.*
