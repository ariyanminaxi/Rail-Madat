# Maintenance Intelligence Service

## Purpose

The Maintenance Intelligence Service provides AI classification and decision-support for railway maintenance. It receives validated complaint data from the Maintenance Data Service and produces:

1. Department classification
2. Fault-category classification
3. Severity prediction
4. Base-priority recommendation
5. Workflow-sensitive final-priority calculation
6. Confidence evaluation
7. Human-review recommendation
8. Plain-language explanations

## Architecture

```
Maintenance Data Service
      ↓
Feature Construction
      ↓
Maintenance Classifier
      ↓
Confidence Assessment
      ↓
Maintenance Prioritization Engine
      ↓
Explanation Generator
      ↓
FastAPI response
```

## How to Train

```bash
python -m ml.maintenance_intelligence.training.generate_dataset
python -m ml.maintenance_intelligence.training.train_classifier
python -m ml.maintenance_intelligence.training.evaluate_model
```

## How to Run Tests

```bash
pytest ml/maintenance_intelligence/tests -q
```

## Python Requirements

- Python >= 3.9
- scikit-learn >= 1.3
- pandas >= 2.0
- numpy >= 1.24
- joblib >= 1.3
- pydantic >= 2.0
