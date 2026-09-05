# Independent source-template protocol

External templates are staged under `artifacts/contributions/`, which is ignored by
Git until privacy, authorship, and license checks are complete. A contribution consists
of one Python file and one JSON metadata file with the same base name.

Example `friend_case_01.json`:

```json
{
  "author_id": "researcher_b",
  "style_id": "researcher_b_style_1",
  "template_family": "custom_preprocessing_pair",
  "fault_family": "preprocessing_before_split",
  "variant": "faulty",
  "source_file": "friend_case_01.py",
  "license_statement": "I authored this example and permit its use in this research project."
}
```

The author should submit matched clean and faulty versions when possible. Code must be
written independently, parse as Python, and avoid comments or variable names that say
whether it is clean or faulty. The metadata key is kept away from blinded reviewers.

Validate and combine contributions with:

```bash
python scripts/build_source_index.py \
  --contributions artifacts/contributions \
  --output artifacts/source_pilot_external/cases.jsonl
```

The combined index should then be used to create a new blinded review package. Do not
copy an existing repository template and rename variables; that does not constitute an
independent structure.

```bash
python scripts/export_blind_review.py \
  --source-index artifacts/source_pilot_external/cases.jsonl \
  --output artifacts/blind_review_external \
  --salt 'a-private-random-sentence-shared-by-neither-reviewer'
```
