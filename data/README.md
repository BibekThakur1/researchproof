# Data policy

The pilot uses datasets bundled with scikit-learn so that it runs without accounts, private data, or manual downloads.

Later benchmark datasets should come from OpenML or the UCI Machine Learning Repository. Every addition must record:

- canonical dataset name and stable identifier;
- source URL and retrieval date;
- license and redistribution conditions;
- target column and task definition;
- row, column, and class counts;
- missing-value and duplicate statistics;
- checksum of the untouched source file;
- any exclusion or cleaning decision.

Raw and cached datasets are ignored by Git. A versioned manifest and retrieval script—not copied data—should make acquisition reproducible.

