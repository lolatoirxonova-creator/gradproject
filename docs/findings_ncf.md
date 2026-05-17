# Findings — Neural Collaborative Filtering (NeuMF)

> Fill this in after running `notebooks/05_neural_cf.ipynb`. Pull from `outputs/neural_cf/results.json`.

## Training

| Setting | Value |
|---|---|
| Device | [`cuda` / `cpu`] |
| Sample size | [N] transactions |
| Epochs | [N] |
| Final BCE loss | [value] |
| Total training time | [minutes] |

[1 sentence on whether the loss curve flattened (good) or was still falling (under-trained).]

## Metrics (warm users, top-10)

| Metric | NeuMF | Best classical (from Notebook 04) |
|---|---|---|
| Precision@10 | [value] | [value] |
| Recall@10 | [value] | [value] |
| NDCG@10 | [value] | [value] |
| MAP@10 | [value] | [value] |
| HitRate@10 | [value] | [value] |

## Discussion (3 paragraphs)

**1. Does NCF beat the classical hybrid?** [Quote numbers. State the answer plainly — yes or no.]

**2. Cost–benefit analysis.** [If NCF wins: by how much, and what does it cost in compute / engineering complexity? If NCF loses or ties: cite Rendle et al. (2020) "NCF vs MF revisited" — this is exactly the finding their paper predicts on many datasets.]

**3. Practical implication for a small Uzbek marketplace.** [Would the operational cost of NCF (PyTorch in production, GPU inference, more code to maintain) be justified by the measured uplift on this data? Answer plainly. This honesty is M5 / D3 evidence.]

## What this tells the report

This single-split result feeds into the cross-validated evaluation in Notebook 06, but **NCF itself is not cross-validated** because retraining is too expensive on the available compute. The validity discussion in Chapter 5 must call this out explicitly.

## Figures

- `outputs/neural_cf/training_loss.png` — convergence
- `outputs/neural_cf/four_way_comparison.png` — final bar chart with all 4 algorithms
