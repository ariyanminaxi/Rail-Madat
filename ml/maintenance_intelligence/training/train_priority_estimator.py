"""Optional priority estimator training.

For the MVP, priority is determined by a transparent rule engine in
app/maintenance_intelligence/prioritization/priority_engine.py.
This module exists for future experimentation.
"""


def train_priority_estimator_placeholder():
    """Placeholder for future priority estimator training."""
    print("=" * 60)
    print("Maintenance Intelligence — Priority Estimator Training (MVP: Rule Engine)")
    print("=" * 60)
    print()
    print("The MVP uses a deterministic rule engine for priority escalation.")
    print("See: app/maintenance_intelligence/prioritization/priority_engine.py")
    print()
    print("Benefits of the rule-based approach:")
    print("  - Safety overrides are always applied")
    print("  - Workflow escalations are transparent and auditable")
    print("  - No training data required")
    print()
    print("Skipping — using rule engine for priority.")


if __name__ == "__main__":
    train_priority_estimator_placeholder()
