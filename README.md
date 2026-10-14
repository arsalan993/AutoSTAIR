# AutoSTAIR

**Published project report:** https://autostair-rag-benchmark.handywolf1.chatgpt.site

The LinkedIn carousel and post draft are in `output/pdf/` and `share/`.

AutoSTAIR is a resource-light RAG benchmark comparing fixed-size chunk retrieval
with two-stage retrieval through a document's existing table of contents. It does
not ask an AI model to generate headings, summaries, paragraph indexes, or a new
hierarchy.

The first case study uses the World Bank's *World Development Report 2024: The
Middle-Income Trap*. The full 276-page report has a detailed machine-readable
authored outline and is published under CC BY 3.0 IGO. Both retrieval methods use
the same source text, BGE-small-en-v1.5 embeddings, question set, evidence-token
budget, answer prompt, and GPT-OSS 20B generator. Retrieval metrics and generated-
answer quality are reported separately.

Generation allows up to 900 completion tokens so GPT-OSS has enough room for its
reasoning and a complete cited answer. Evaluation starts generation calls at least
20 seconds apart and supports checkpoints, so an interrupted run can resume without
repeating completed API calls.

## What is implemented

- PDF extraction from an authored, embedded table of contents using PyMuPDF.
- Configurable removal of auxiliary box/figure/table indexes that duplicate pages.
- 400-token passages with 80-token overlap.
- Local FAISS cosine indexes for passages and authored sections.
- Flat retrieval over every passage.
- Structured retrieval that selects existing sections before ranking passages
  inside those sections.
- Optional grounded generation through Groq's `openai/gpt-oss-20b`.
- Recall@1/3/5, MRR, latency, token-use, JSONL, and CSV outputs.
- Randomized A/B export for blinded answer judging.
- A Streamlit dashboard for side-by-side questions, generated answers, retrieval
  evidence, benchmark metrics, question-level evaluation, and corpus inspection.

## Setup

Requirements: Python 3.11 or newer. Python 3.12 is recommended.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
```

Follow [the data setup instructions](data/README.md), then build the indexes:

```sh
autostair build
```

Compare retrieval for one question:

```sh
autostair query "How do preschoolers react when adults discourage autonomy?"
```

Add `--generate` to use Groq. Put the API key in `.env`; it is read by the
backend and excluded from Git.

Run the fixed question set and create the blinded judging file:

```sh
autostair evaluate --generate --resume
autostair blind
```

Start the comparison interface:

```sh
streamlit run app.py
```

The dashboard has four pages inside one browser window:

- **Overview** explains both methods and charts the latest aggregate results.
- **Ask & compare** retrieves evidence side by side and can generate grounded answers.
- **Chunk data** exposes every flat passage and shows how those same passages are
  grouped beneath the publisher-authored section index.
- **Evaluation** runs the pilot benchmark and exposes every answer, metric, and evidence set.
- **Document & data** lists authored sections and benchmark questions and provides
  downloads for the source PDF and result files.

## Experiment controls

The included twenty-question pilot set is for exercising the pipeline and making
configuration decisions. Do not report it as the final benchmark. Prepare a
separate frozen evaluation set with manually checked section IDs, evidence, and
reference answers. Both methods must keep the same evidence-token budget and
generator settings.

The World Bank report is licensed separately under CC BY 3.0 IGO. Keep source
files out of Git and preserve the attribution in [the data instructions](data/README.md).
See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full methodology and
[docs/JUDGING.md](docs/JUDGING.md) for blinded review.

AutoSTAIR is inspired by IBM's STAIR research. It is a practical benchmark, not a
reproduction of STAIR's fine-tuned generative retriever.
