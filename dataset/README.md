# Dataset setup (important)

This repository intentionally does **not** contain a fabricated or unlabeled-as-real medical dataset. The `manifest.csv` file is a starter manifest. Add a properly licensed, de-identified retinal fundus dataset and update the manifest.

## Suggested public research datasets

- **APTOS 2019 Blindness Detection**: diabetic-retinopathy grading from fundus images; check Kaggle competition terms and the dataset's license/terms before use.
- **EyePACS / Kaggle diabetic retinopathy**: commonly used for research; review the exact competition rules, usage rights, and image provenance.
- **Messidor / Messidor-2**: research datasets; verify the access and license terms for your intended use.
- **ODIR-5K**: multi-label ocular disease dataset; verify access terms and class definitions.

Do not mix datasets or labels without checking the task definition. Obtain institutional/mentor approval where required, remove patient identifiers, split at patient level where possible, and document data provenance.

## Manifest format

`image_path,label,split,source,notes`

Example row (illustrative only, not an included image):

`images/example_001.png,referable_dr,train,licensed_dataset_name,anonymized`

Possible labels depend on the dataset and model, for example `no_dr`, `mild_dr`, `moderate_dr`, `severe_dr`, `proliferative_dr`. Do not assume these labels are interchangeable across datasets. Keep a separate test set and evaluate sensitivity, specificity, AUROC, calibration, and subgroup performance before reporting metrics.
