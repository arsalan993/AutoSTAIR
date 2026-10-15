I’ve just wrapped up a small RAG experiment I called AutoSTAIR.

The question started off pretty simply: if a long document already has a useful table of contents, can a RAG system use that structure to find better evidence than it would with ordinary fixed-size chunks?

The idea came from IBM Research's paper, "STAIR: A novel dataset and LLM based retriever for document structure augmentation." Their work predicts the relevant leaf section from a document's full table of contents. I did not try to reproduce their training setup. Instead, I built a resource-light benchmark around one public document: the World Bank's 276-page World Development Report 2024.

I compared two pipelines over the same document, questions, embeddings, generator, and retrieval depth:

1. Flat RAG: search all 395 fixed-size chunks directly.
2. Index-guided RAG: first select one of 54 authored sections, then search only inside that section.

I tested 20 diverse questions and manually reviewed the answers using a blinded rubric for correctness, grounding, completeness, and citation quality.

The result was more mixed than I expected.

Index-guided retrieval had a slightly better Hit@1 score (0.60 vs 0.55) and won 8 answer comparisons against 6 for flat retrieval, with 6 ties. It was often more focused and easier to audit. But flat retrieval recovered relevant evidence more reliably at larger depths: Hit@3 was 0.85 vs 0.80, and Hit@5 was 0.90 vs 0.80. Its overall answer-quality score was also higher (4.85 vs 4.61) because the structured pipeline completely missed two cross-section questions.

My main takeaway is that document structure is a useful routing signal, but making a hard decision to search only one section can become a bottleneck. If I take this further, I would use the index to focus the search while keeping a small global retrieval path as a fallback.

This is only one report and 20 questions, so I’m not treating it as a universal conclusion. For me, it is a useful result and a clear direction for the next experiment. I’ve published the dashboard, retrieval data, evaluation output, and methodology for anyone who wants to inspect the details.

Code: https://github.com/arsalan993/AutoSTAIR
Project report: https://autostair-rag-benchmark.handywolf1.chatgpt.site

#RAG #GenerativeAI #InformationRetrieval #LLM #MachineLearning #AIEngineering
