# Benchmark specification, version 0.1

## Unit of analysis

One benchmark case contains a clean pipeline, one controlled faulty variant, a machine-readable manifest, the expected fault label, the intended repair, and runtime artifacts. Both pipelines must use the same prediction task and evaluation split unless the split itself is the injected fault.

## Required manifest fields

```text
case_id
dataset_id and dataset_checksum
template_id and template_version
fault_family and injector_version
seed and split policy
model and hyperparameters
expected evidence
expected repair
environment lock identifier
```

The reference implementation lives in `researchproof.manifest.BenchmarkManifest`.
Its `case_id` is derived from a canonical serialization of every field, so changing
the seed, split, dataset checksum, template, fault definition, or environment lock
produces a different identifier. A stored identifier that no longer matches its
contents is rejected as a tampered or stale manifest.

## Leakage prevention in the detector study

Cases derived from one source dataset may not be divided between detector training and testing. Closely related pipeline templates must remain in one partition. Injector-specific strings and filenames must not reveal the label. Evaluation includes a leave-one-fault-family-out protocol.

## Annotation procedure

Two reviewers independently inspect a sample without seeing the injector label. They answer: Is the experiment valid for its stated task? Which evidence supports the decision? What minimal change would repair it? Disagreements are retained and adjudicated with written reasoning.

## Versioning rule

Once a benchmark release is used for a reported table, its cases and partitions are immutable. Corrections create a new version with a changelog and a mapping from old case identifiers.
