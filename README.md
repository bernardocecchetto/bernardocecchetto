<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
  <img alt="Bernardo Cecchetto, AI Engineer. I take AI from prototype to production." src="./assets/hero-light.svg" width="100%">
</picture>

I build AI products that have to work outside the demo: multi-agent systems, RAG and document intelligence, plus the backend, queues and deployment that keep them running. For 4+ years I've done this in domains where a wrong answer is expensive, from US tax filing to medical imaging.

My path started in physics, with a BSc in Medical Physics and an MSc in Information Technology, which still shapes how I work: measure first, then trust.

## What I ship

| | |
|:---|:---|
| **Multi-agent systems** | Orchestrators and specialist agents, human-in-the-loop pause and resume, typed MCP tools, agents that see and drive a React UI through AG-UI |
| **RAG and search** | Hybrid retrieval with pgvector, Reciprocal Rank Fusion and BGE-M3, RAG assistants on top of speech-to-text |
| **Document intelligence** | OCR pipelines with vision LLMs on AWS SageMaker, typed extraction with BAML |
| **Models** | Transformer architectures, LLM fine-tuning, model routing and fallback for latency and cost |
| **Production engineering** | FastAPI, WebSockets, Docker, Postgres job queues with per-tenant fairness, CI with deterministic Playwright gates and AI-assisted PR review |

**Stack:** Python · LangGraph · LangChain · Amazon Bedrock · AWS SageMaker · Gemini · FastAPI · PostgreSQL · pgvector · Docker · React

## Selected work

<details>
<summary><b>AI tax filing platform</b> · EzTaxReturn</summary>
<br>
Multi-agent systems for US tax filing on Amazon Bedrock, LangChain and LangGraph. An orchestrator delegates to domain specialists, the agent knows each screen and field the user is on, and uploaded tax documents flow through an OCR pipeline into the forms.
</details>

<details>
<summary><b>WhatsApp automation for auto repair shops</b> · multi-tenant</summary>
<br>
Customer service agents on Gemini, running on-premises with Docker and PostgreSQL. A Postgres-backed job queue keeps tenants fair, and model routing with fallback holds latency down for real-time conversations.
</details>

<details>
<summary><b>GenAI for Agile automation</b> · Eldorado Research Institute, for Dell</summary>
<br>
Generative AI applied to automating Agile workflows.
</details>

<details>
<summary><b>Speech-to-text and RAG assistants</b> · Peers Consulting</summary>
<br>
Speech-to-text pipelines and retrieval-based assistants.
</details>

<details>
<summary><b>Computer vision for medical imaging</b> · Med.Place</summary>
<br>
Deep learning for medical images, building on my research into automated image quality control for mammography equipment.
</details>

<!--STATS:START-->
<!--STATS:END-->

## Let's talk

Building something with AI that has to survive contact with real users? Reach me at [cecchetto.bernardo@gmail.com](mailto:cecchetto.bernardo@gmail.com) · [Hugging Face](https://huggingface.co/bernardocecchetto) · [X](https://twitter.com/Ber_Cecchetto)
