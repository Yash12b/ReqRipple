import json
from typing import Dict, List, Any


class DiffResult:
    def __init__(
        self,
        field_name: str,
        old_value: str,
        new_value: str,
        diff_type: str,
        change_category: str,
    ):
        self.field_name = field_name
        self.old_value = old_value
        self.new_value = new_value
        self.diff_type = diff_type
        self.change_category = change_category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "diff_type": self.diff_type,
            "change_category": self.change_category,
        }


class ChangeClassifier:
    @staticmethod
    def _classify_field_change(field_name: str, old_val: Any, new_val: Any) -> str:
        f = field_name.lower()
        if "security" in f or "privacy" in f or "auth" in str(new_val).lower():
            return "SECURITY_OR_PRIVACY_CHANGE"
        elif "acceptance_criteria" in f:
            return "ACCEPTANCE_CRITERIA_CHANGE"
        elif "priority" in f or "criticality" in f:
            return "PRIORITY_CHANGE"
        elif "performance" in f or "constraint" in f:
            return "NON_FUNCTIONAL_CONSTRAINT_CHANGE"
        elif "title" in f:
            return "FUNCTIONAL_SCOPE_CHANGE"
        elif "description" in f:
            # Check length/wording difference
            old_words = set(str(old_val).lower().split())
            new_words = set(str(new_val).lower().split())
            diff_ratio = len(old_words.symmetric_difference(new_words)) / max(1, len(old_words.union(new_words)))
            if diff_ratio < 0.25:
                return "WORDING_ONLY"
            return "FUNCTIONAL_SCOPE_CHANGE"
        return "FUNCTIONAL_SCOPE_CHANGE"

    @staticmethod
    def compare_requirement_versions(
        current_data: Dict[str, Any],
        proposed_data: Dict[str, Any],
    ) -> List[DiffResult]:
        diffs: List[DiffResult] = []

        all_keys = set(current_data.keys()).union(proposed_data.keys())
        # Filter to relevant requirement fields
        tracked_keys = [
            "title",
            "description",
            "acceptance_criteria",
            "priority",
            "criticality",
            "rationale",
        ]

        for key in tracked_keys:
            if key not in all_keys:
                continue

            old_val = current_data.get(key)
            new_val = proposed_data.get(key)

            # Normalize values for comparison
            old_str = json.dumps(old_val, sort_keys=True) if isinstance(old_val, (list, dict)) else str(old_val or "")
            new_str = json.dumps(new_val, sort_keys=True) if isinstance(new_val, (list, dict)) else str(new_val or "")

            if old_val is None and new_val is not None:
                diff_type = "ADDED"
                category = ChangeClassifier._classify_field_change(key, old_val, new_val)
            elif old_val is not None and new_val is None:
                diff_type = "REMOVED"
                category = "DELETION_OR_RETIREMENT"
            elif old_str != new_str:
                diff_type = "MODIFIED"
                category = ChangeClassifier._classify_field_change(key, old_val, new_val)
            else:
                diff_type = "UNCHANGED"
                category = "WORDING_ONLY"

            if diff_type != "UNCHANGED":
                diffs.append(
                    DiffResult(
                        field_name=key,
                        old_value=old_str,
                        new_value=new_str,
                        diff_type=diff_type,
                        change_category=category,
                    )
                )

        return diffs
