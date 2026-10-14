from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from autostair.config import load_settings
from autostair.evaluation import load_questions, run_evaluation
from autostair.generation import AnswerGenerator
from autostair.retrieval import Retriever, format_evidence


st.set_page_config(page_title="AutoSTAIR Dashboard", page_icon="📚", layout="wide")


@st.cache_resource
def resources():
    settings = load_settings("configs/default.yaml")
    return settings, Retriever(settings)


@st.cache_data
def read_json(path: str) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


@st.cache_data
def read_jsonl(path: str) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []
    with source.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


@st.cache_data
def read_csv(path: str) -> pd.DataFrame:
    source = Path(path)
    return pd.read_csv(source) if source.exists() else pd.DataFrame()


def evidence_card(hit: dict[str, Any], rank: int) -> None:
    label = (
        f"#{rank} · {hit['section_path']} · pages "
        f"{hit['page_start']}–{hit['page_end']} · score {hit['score']:.4f}"
    )
    with st.expander(label, expanded=rank == 1):
        st.caption(f"Passage ID: {hit['passage_id']} · Section ID: {hit['section_id']}")
        st.write(hit["text"])


def result_panel(
    label: str,
    method: str,
    question: str,
    hits: list[dict[str, Any]],
    latency_ms: float,
    generator: AnswerGenerator | None,
    token_budget: int,
) -> None:
    st.subheader(label)
    evidence = format_evidence(hits, token_budget)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Retrieval", f"{latency_ms:.1f} ms")
    metric_columns[1].metric("Passages", len(hits))
    metric_columns[2].metric("Sections", len({hit["section_id"] for hit in hits}))

    if generator:
        started = time.perf_counter()
        try:
            answer, usage = generator.answer(question, evidence)
            generation_ms = (time.perf_counter() - started) * 1000
            st.markdown("#### Grounded answer")
            st.markdown(answer)
            st.caption(
                f"Generation: {generation_ms:.0f} ms · "
                f"{usage['total_tokens']} total model tokens"
            )
        except Exception as error:
            st.error(f"Answer generation failed: {error}")
    else:
        st.info("Answer generation is off. The retrieved evidence is shown below.")

    st.markdown("#### Retrieved evidence")
    for rank, hit in enumerate(hits, start=1):
        evidence_card(hit, rank)
    st.download_button(
        "Download evidence",
        evidence,
        file_name=f"{method}-evidence.txt",
        mime="text/plain",
        key=f"download-{method}",
        width="stretch",
    )


try:
    settings, retriever = resources()
except Exception as error:
    st.error(f"The FAISS indexes could not be loaded: {error}")
    st.code("autostair build")
    st.stop()

artifact_dir = settings.resolve(settings.paths["artifacts_dir"])
manifest_path = artifact_dir / "manifest.json"
results_dir = artifact_dir / "results"
evaluation_path = results_dir / "evaluation.jsonl"
summary_path = results_dir / "summary.csv"
judgments_path = results_dir / "manual_judgments.json"
questions_path = settings.resolve(settings.paths["questions_path"])
pdf_path = settings.resolve(settings.document["pdf_path"])
manifest = read_json(str(manifest_path))

with st.sidebar:
    st.title("📚 AutoSTAIR")
    st.caption("A transparent RAG retrieval benchmark")
    st.divider()
    st.markdown("**Document**")
    st.write(settings.document["title"])
    st.markdown("**Embedding model**")
    st.code(settings.embedding["model"], language=None)
    st.markdown("**Generator**")
    st.code(settings.generation["model"], language=None)
    st.divider()
    st.caption("No model is used to create or rewrite the document index.")

st.title("AutoSTAIR Benchmark Dashboard")
st.caption(
    "Compare standard flat chunks with two-stage retrieval through the report's "
    "authored table of contents."
)

overview_tab, compare_tab, chunks_tab, evaluation_tab, data_tab = st.tabs(
    ["Overview", "Ask & compare", "Chunk data", "Evaluation", "Document & data"]
)

with overview_tab:
    st.subheader("Experiment at a glance")
    columns = st.columns(4)
    columns[0].metric("Report pages", 276)
    columns[1].metric("Authored sections", manifest["section_count"])
    columns[2].metric("Passages", manifest["passage_count"])
    columns[3].metric(
        "Chunking",
        f"{manifest['chunk_size_tokens']} / {manifest['chunk_overlap_tokens']}",
        help="Chunk size / overlap in estimated tokens",
    )

    st.markdown("### What is being compared")
    method_columns = st.columns(2)
    with method_columns[0]:
        st.markdown("#### Flat chunks")
        st.write(
            "The question is embedded and compared directly with every passage in "
            "the report. The five closest passages become the evidence."
        )
    with method_columns[1]:
        st.markdown("#### Existing document index")
        st.write(
            "The question first selects authored report sections. Passages are then "
            "ranked only inside those sections. The original headings are preserved."
        )

    summary = read_csv(str(summary_path))
    if not summary.empty:
        st.markdown("### Latest pilot retrieval results")
        display = summary.rename(
            columns={
                "method": "Method",
                "hit_at_1": "Hit@1",
                "hit_at_3": "Hit@3",
                "hit_at_5": "Hit@5",
                "reciprocal_rank": "MRR",
                "questions": "Questions",
            }
        )
        st.dataframe(display, hide_index=True, width="stretch")
        chart_data = summary.melt(
            id_vars="method",
            value_vars=["hit_at_1", "hit_at_3", "hit_at_5", "reciprocal_rank"],
            var_name="metric",
            value_name="score",
        )
        figure = px.bar(
            chart_data,
            x="metric",
            y="score",
            color="method",
            barmode="group",
            range_y=[0, 1],
            labels={"metric": "Metric", "score": "Score", "method": "Method"},
        )
        st.plotly_chart(figure, width="stretch")
        st.warning(
            "These twenty questions are a development pilot. They validate the pipeline "
            "but are not the final publishable benchmark."
        )

with compare_tab:
    st.subheader("Ask the report")
    pilot_questions = load_questions(questions_path)
    suggested = [question["question"] for question in pilot_questions]
    selected = st.selectbox(
        "Start with a pilot question",
        ["Write my own question", *suggested],
    )
    default_question = "" if selected == "Write my own question" else selected
    question = st.text_area(
        "Question",
        value=default_question,
        placeholder="Ask something answered by the World Bank report",
        height=90,
    )
    option_columns = st.columns([1, 2])
    generate = option_columns[0].checkbox("Generate answers with Groq", value=False)
    option_columns[1].caption(
        "Generation uses the same model, prompt, temperature, and evidence budget "
        "for both retrieval methods."
    )

    if st.button("Compare both methods", type="primary", disabled=not question.strip()):
        generator = None
        if generate:
            try:
                generator = AnswerGenerator(settings)
            except Exception as error:
                st.error(str(error))
                st.stop()

        with st.spinner("Embedding the question and retrieving evidence…"):
            flat_started = time.perf_counter()
            flat_hits = retriever.flat(question)
            flat_ms = (time.perf_counter() - flat_started) * 1000
            structured_started = time.perf_counter()
            structured_hits = retriever.structured(question)
            structured_ms = (time.perf_counter() - structured_started) * 1000

        token_budget = int(settings.retrieval["evidence_token_budget"])
        result_columns = st.columns(2)
        with result_columns[0]:
            result_panel(
                "Flat chunks", "flat", question, flat_hits, flat_ms, generator, token_budget
            )
        with result_columns[1]:
            result_panel(
                "Existing document index",
                "structured",
                question,
                structured_hits,
                structured_ms,
                generator,
                token_budget,
            )

with chunks_tab:
    st.subheader("How the document is represented")
    st.info(
        "This is a controlled retrieval experiment. Both methods use the same 395 "
        "passage chunks. Flat retrieval searches all chunks directly. Indexed "
        "retrieval first selects an authored section, then searches only the chunks "
        "belonging to the selected sections. This keeps chunk text and embeddings "
        "constant while testing the effect of the document index."
    )

    passage_rows = retriever.passages.records
    section_rows = retriever.sections.records
    chunk_metrics = st.columns(4)
    chunk_metrics[0].metric("Passage chunks", len(passage_rows))
    chunk_metrics[1].metric("Authored sections", len(section_rows))
    chunk_metrics[2].metric("Maximum chunk size", manifest["chunk_size_tokens"])
    chunk_metrics[3].metric("Token overlap", manifest["chunk_overlap_tokens"])

    flat_chunks_tab, indexed_chunks_tab = st.tabs(
        ["Flat chunk corpus", "Authored index and member chunks"]
    )

    with flat_chunks_tab:
        st.markdown("### All chunks searched by the flat baseline")
        st.caption(
            "Each row is independently embedded. Section headings are metadata for "
            "inspection and evaluation; they are not included in flat passage embeddings."
        )
        flat_frame = pd.DataFrame(
            [
                {
                    "passage_id": row["passage_id"],
                    "section_id": row["section_id"],
                    "section": row["section_path"],
                    "pages": f"{row['page_start']}–{row['page_end']}",
                    "token_start": row["token_start"],
                    "token_end": row["token_end"],
                    "tokens": row["token_end"] - row["token_start"],
                    "text": row["text"],
                }
                for row in passage_rows
            ]
        )
        flat_filter = st.text_input(
            "Filter flat chunks",
            placeholder="Search passage ID, section heading, or text",
            key="flat-chunk-filter",
        )
        shown_flat = flat_frame
        if flat_filter:
            mask = (
                flat_frame["passage_id"].str.contains(flat_filter, case=False, na=False)
                | flat_frame["section"].str.contains(flat_filter, case=False, na=False)
                | flat_frame["text"].str.contains(flat_filter, case=False, na=False)
            )
            shown_flat = flat_frame[mask]
        st.caption(f"Showing {len(shown_flat)} of {len(flat_frame)} chunks")
        st.dataframe(
            shown_flat,
            hide_index=True,
            width="stretch",
            height=420,
            column_config={"text": st.column_config.TextColumn("Chunk text", width="large")},
        )
        selected_passage_id = st.selectbox(
            "Inspect one flat chunk",
            shown_flat["passage_id"].tolist(),
            key="flat-passage-selector",
        ) if not shown_flat.empty else None
        if selected_passage_id:
            selected_passage = next(
                row for row in passage_rows if row["passage_id"] == selected_passage_id
            )
            st.code(selected_passage["text"], language=None, wrap_lines=True)
            st.caption(
                f"{selected_passage['section_path']} · pages "
                f"{selected_passage['page_start']}–{selected_passage['page_end']} · "
                f"tokens {selected_passage['token_start']}–{selected_passage['token_end']}"
            )
        st.download_button(
            "Download all passage chunks",
            (artifact_dir / "passages.json").read_bytes(),
            file_name="passages.json",
            mime="application/json",
        )

    with indexed_chunks_tab:
        st.markdown("### Publisher-authored sections and their chunks")
        st.caption(
            "The first retrieval stage embeds the authored heading path plus the first "
            "2,400 characters of source section text. It does not use generated headings "
            "or summaries. The second stage ranks the same passage chunks shown above."
        )
        section_options = {row["section_id"]: row for row in section_rows}
        chosen_section_id = st.selectbox(
            "Choose an authored section",
            list(section_options),
            format_func=lambda section_id: (
                f"{section_id} — {section_options[section_id]['path']} "
                f"(pages {section_options[section_id]['page_start']}–"
                f"{section_options[section_id]['page_end']})"
            ),
            key="indexed-section-selector",
        )
        chosen_section = section_options[chosen_section_id]
        member_chunks = [
            row for row in passage_rows if row["section_id"] == chosen_section_id
        ]
        section_metrics = st.columns(3)
        section_metrics[0].metric("Section level", chosen_section["level"])
        section_metrics[1].metric("Member chunks", len(member_chunks))
        section_metrics[2].metric(
            "Page range",
            f"{chosen_section['page_start']}–{chosen_section['page_end']}",
        )
        st.markdown(f"#### {chosen_section['path']}")
        with st.expander("Source text extracted for this section"):
            st.text(chosen_section["text"])
        st.markdown("#### Passage chunks inside this section")
        member_frame = pd.DataFrame(
            [
                {
                    "passage_id": row["passage_id"],
                    "token_start": row["token_start"],
                    "token_end": row["token_end"],
                    "tokens": row["token_end"] - row["token_start"],
                    "text": row["text"],
                }
                for row in member_chunks
            ]
        )
        st.dataframe(
            member_frame,
            hide_index=True,
            width="stretch",
            height=420,
            column_config={"text": st.column_config.TextColumn("Chunk text", width="large")},
        )
        if member_chunks:
            indexed_passage_id = st.selectbox(
                "Inspect one member chunk",
                [row["passage_id"] for row in member_chunks],
                key="indexed-passage-selector",
            )
            indexed_passage = next(
                row for row in member_chunks if row["passage_id"] == indexed_passage_id
            )
            st.code(indexed_passage["text"], language=None, wrap_lines=True)
        st.download_button(
            "Download authored section index",
            (artifact_dir / "sections.json").read_bytes(),
            file_name="sections.json",
            mime="application/json",
        )

with evaluation_tab:
    st.subheader("Benchmark evaluation")
    controls = st.columns([1, 1, 2])
    run_generation = controls[0].checkbox(
        "Generate all answers",
        value=False,
        help="Requires GROQ_API_KEY and makes two model calls per question.",
    )
    if controls[1].button("Run benchmark", width="stretch"):
        try:
            with st.spinner("Running both retrieval methods across the question set…"):
                run_evaluation(
                    settings,
                    generate_answers=run_generation,
                    resume=True,
                )
            read_jsonl.clear()
            read_csv.clear()
            st.success("Evaluation completed and the dashboard data was refreshed.")
        except Exception as error:
            st.error(f"Evaluation failed: {error}")

    rows = read_jsonl(str(evaluation_path))
    if not rows:
        st.info("No evaluation output exists yet. Run the benchmark above.")
    else:
        frame = pd.DataFrame(rows)
        metric_columns = st.columns(4)
        metric_columns[0].metric("Questions", frame["question_id"].nunique())
        metric_columns[1].metric("Evaluation rows", len(frame))
        metric_columns[2].metric("Average retrieval", f"{frame['retrieval_ms'].mean():.1f} ms")
        answered = int((frame["answer"].fillna("").str.len() > 0).sum())
        metric_columns[3].metric("Generated answers saved", answered)
        if answered == 0:
            st.warning(
                "This saved run contains retrieval metrics only. Enable “Generate all "
                "answers” and run the benchmark to populate answer evaluation data."
            )

        if judgments_path.exists():
            judgments = read_json(str(judgments_path))
            judge_summary = judgments["summary"]
            st.markdown("### Blinded manual LLM-as-judge results")
            judge_columns = st.columns(4)
            judge_columns[0].metric("Indexed wins", judge_summary["structured"]["wins"])
            judge_columns[1].metric("Flat wins", judge_summary["flat"]["wins"])
            judge_columns[2].metric("Ties", judge_summary["ties"])
            judge_columns[3].metric(
                "Indexed / flat quality",
                f"{judge_summary['structured']['overall']:.2f} / "
                f"{judge_summary['flat']['overall']:.2f}",
            )
            judge_frame = pd.DataFrame(
                [
                    {"method": "Flat chunks", **judge_summary["flat"]},
                    {"method": "Existing index", **judge_summary["structured"]},
                ]
            )
            st.dataframe(judge_frame, hide_index=True, width="stretch")
            st.caption(
                "Scores are 1–5. Answers were labeled system A/B during review; "
                "method identities were revealed only after scores and preferences were saved."
            )

        selected_id = st.selectbox(
            "Inspect a question",
            frame["question_id"].drop_duplicates().tolist(),
            format_func=lambda value: (
                f"{value} — {frame.loc[frame['question_id'] == value, 'question'].iloc[0]}"
            ),
        )
        selected_rows = frame[frame["question_id"] == selected_id]
        first = selected_rows.iloc[0]
        st.markdown(f"### {first['question']}")
        if first.get("reference_answer"):
            st.info(f"Reference answer: {first['reference_answer']}")
        st.caption(f"Expected section IDs: {', '.join(first['gold_section_ids'])}")
        if judgments_path.exists():
            selected_judgment = next(
                item
                for item in judgments["per_question"]
                if item["question_id"] == selected_id
            )
            st.success(
                f"Manual judge: {selected_judgment['winner']} · "
                f"{selected_judgment['notes']}"
            )

        answer_columns = st.columns(2)
        for column, (_, row) in zip(answer_columns, selected_rows.iterrows()):
            with column:
                label = "Flat chunks" if row["method"] == "flat" else "Existing index"
                st.markdown(f"#### {label}")
                scores = st.columns(4)
                scores[0].metric("Hit@1", int(row["hit_at_1"]))
                scores[1].metric("Hit@3", int(row["hit_at_3"]))
                scores[2].metric("Hit@5", int(row["hit_at_5"]))
                scores[3].metric("MRR", f"{row['reciprocal_rank']:.2f}")
                st.caption(
                    "Retrieved sections: "
                    + ", ".join(dict.fromkeys(row["retrieved_section_ids"]))
                )
                if row.get("answer"):
                    st.markdown("**Generated answer**")
                    st.markdown(row["answer"])
                    st.caption(
                        f"Generation: {row['generation_ms']:.0f} ms · "
                        f"{row['total_tokens']} tokens"
                    )
                else:
                    st.info("No generated answer is saved for this run.")
                with st.expander("Evidence supplied to the generator"):
                    st.text(row["evidence"])

        st.download_button(
            "Download complete evaluation JSONL",
            evaluation_path.read_bytes(),
            file_name="evaluation.jsonl",
            mime="application/x-ndjson",
        )

with data_tab:
    st.subheader("Document and benchmark data")
    document_columns = st.columns([2, 1])
    with document_columns[0]:
        st.markdown(f"### {settings.document['title']}")
        st.write(
            "The benchmark uses the report's embedded, publisher-authored table of "
            "contents. Auxiliary figure, table, map, and box indexes are excluded "
            "because they point back into pages already covered by report sections."
        )
    with document_columns[1]:
        if pdf_path.exists():
            st.download_button(
                "Download source PDF",
                pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
                width="stretch",
            )

    section_rows = retriever.sections.records
    section_frame = pd.DataFrame(
        [
            {
                "section_id": row["section_id"],
                "section": row["path"],
                "pages": f"{row['page_start']}–{row['page_end']}",
            }
            for row in section_rows
        ]
    )
    st.markdown("### Authored sections")
    section_search = st.text_input("Filter sections", placeholder="Type part of a heading")
    if section_search:
        section_frame = section_frame[
            section_frame["section"].str.contains(section_search, case=False, na=False)
        ]
    st.dataframe(section_frame, hide_index=True, width="stretch", height=360)

    st.markdown("### Question set")
    question_frame = pd.DataFrame(pilot_questions)
    question_frame["gold_section_ids"] = question_frame["gold_section_ids"].apply(
        lambda values: ", ".join(values)
    )
    st.dataframe(question_frame, hide_index=True, width="stretch")
    st.download_button(
        "Download question set",
        questions_path.read_bytes(),
        file_name=questions_path.name,
        mime="application/x-ndjson",
    )
