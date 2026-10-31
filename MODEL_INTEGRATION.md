# Model integration checklist

The demo intentionally returns `model_status: NOT_CONFIGURED`.

- [ ] Select a dataset whose terms allow the intended use.
- [ ] Document class definitions and any label mapping.
- [ ] De-identify and split at patient level to prevent leakage.
- [ ] Train a CNN and record architecture, preprocessing, seed, dataset version, and weights hash.
- [ ] Validate on a held-out set and preferably an external dataset.
- [ ] Measure sensitivity for sight-threatening disease, specificity, AUROC, calibration, subgroup behavior, and failure cases.
- [ ] Set operating thresholds with clinical input.
- [ ] Add inference to `demo_prediction()` and return model version, class probabilities, limitations, and prediction status.
- [ ] Add a real explanation overlay (for example Grad-CAM) only after sanity checks.
- [ ] Run a privacy/security review and test the entire workflow with a clinician.

A UI progress bar, synthetic scores, or random labels must never be used to imply a disease prediction.
