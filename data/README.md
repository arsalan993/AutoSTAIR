# Data setup

The benchmark uses the World Bank's **World Development Report 2024: The
Middle-Income Trap**. The official full report is 276 pages and contains a
machine-readable authored outline with chapters and subsections.

The source PDF is kept out of Git. Download it from the
[World Bank Open Knowledge Repository](https://openknowledge.worldbank.org/bitstreams/8dca4aff-e0f5-4865-b245-ec9c4583aa60/download)
and save it as:

```text
data/source/world-development-report-2024-full.pdf
```

The report is available under CC BY 3.0 IGO. Cite it as:

> World Bank. 2024. *World Development Report 2024: The Middle-Income Trap.*
> Washington, DC: World Bank. doi:10.1596/978-1-4648-2078-6. License:
> Creative Commons Attribution CC BY 3.0 IGO.

The MIT license for AutoSTAIR's code does not replace the report's license or
the separate rights that may apply to third-party figures and other components.

`questions.pilot.jsonl` contains twenty manually checked development questions for
exercising the pipeline and choosing settings. They are not final benchmark
evidence. Create a separate frozen test set before reporting results. The example
file demonstrates the schema for adding more records.
