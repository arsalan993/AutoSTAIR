I have just finished a small RAG experiment called AutoSTAIR.

The question I wanted to test was simple: if a long document already has a useful table of contents, can that structure help RAG retrieve better evidence than ordinary fixed-size chunking?

The idea came from IBM Research's paper, "STAIR: A novel dataset and LLM based retriever for document structure augmentation." Their work predicts the relevant leaf section from a document's full table of contents. I did not try to reproduce their training setup. Instead, I built a resource-light benchmark around one public document: the World Bank's 276-page World Development Report 2024.

I compared two pipelines over the same document, questions, embeddings, generator, and retrieval depth:

1. Flat RAG: search all 395 fixed-size chunks directly.
2. Index-guided RAG: first select one of 54 authored sections, then search only inside that section.

I tested 20 diverse questions and manually reviewed the answers using a blinded rubric for correctness, grounding, completeness, and citation quality.

The result was more nuanced than "structure always wins."

Index-guided retrieval had a slightly better Hit@1 score (0.60 vs 0.55) and won 8 answer comparisons against 6 for flat retrieval, with 6 ties. It was often more focused and easier to audit. But flat retrieval recovered relevant evidence more reliably at larger depths: Hit@3 was 0.85 vs 0.80, and Hit@5 was 0.90 vs 0.80. Its overall answer-quality score was also higher (4.85 vs 4.61) because the structured pipeline completely missed two cross-section questions.

My main takeaway: document structure is a useful routing signal, but a hard decision to search only one section can become a bottleneck. A hybrid design would be stronger: use the index to focus the search, while keeping a small global retrieval path as a fallback.

This was a small case study, so I see it as evidence for the next experiment rather than a universal conclusion. The project includes the Streamlit interface, retrieval data, evaluation output, and the full methodology.

Code: https://github.com/arsalan993/AutoSTAIR
Project report: https://autostair-rag-benchmark.handywolf1.chatgpt.site

#RAG #GenerativeAI #InformationRetrieval #LLM #MachineLearning #AIEngineering
