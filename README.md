#### CIFAR-10 Logistic Regression (CS 178)

**Course:** CS 178 – Machine Learning & Data Mining  
**Role:** Logistic Regression baseline (my individual contribution)

This repo contains my part of a group project on CIFAR-10 image classification. I implemented a full logistic regression pipeline using PyTorch for data loading and scikit-learn for modeling.

---

#### Pipeline

- Load CIFAR-10 with `torchvision.datasets.CIFAR10`
- Normalize images, convert to NumPy, flatten to 3072-dim vectors
- Standardize features with `StandardScaler`
- Split into train / validation / test sets
- Train multinomial `LogisticRegression` (`solver='lbfgs'`, `penalty='l2'`, tuned `C`, `max_iter`)
- Evaluate with:
  - Train / validation / test accuracy (≈ 41% test)
  - Confusion matrix heatmap
  - Classification report
  - Learning curve (training vs. cross-validation score)

---

#### Hyperparameter Experiments

I ran multiple configurations varying:

- `C` (regularization)
- `max_iter`
- `solver`
- `tol`

Results are stored in a table and visualized to compare training vs. test accuracy and diagnose under/overfitting.

---
