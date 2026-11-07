from typing import List, Dict, Any, Tuple


class ClosureRules:
    @staticmethod
    def evaluate_closure_conditions(
        impact_results: List[Dict[str, Any]],
        remediation_actions: List[Dict[str, Any]],
        test_executions: List[Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """
        Determines whether a change request is eligible to transition to CLOSED.
        Returns: (can_close: bool, blocking_reasons: List[str])
        """
        blocking_reasons: List[str] = []

        # 1. Every impact result must have a reviewed disposition
        unreviewed_results = [
            r for r in impact_results if not r.get("disposition")
        ]
        if unreviewed_results:
            blocking_reasons.append(
                f"{len(unreviewed_results)} impacted artifact(s) have not been reviewed with a recorded disposition."
            )

        # 2. Check remediation actions: All must be DONE or WAIVED
        incomplete_actions = [
            a for a in remediation_actions
            if a.get("status") not in ("DONE", "WAIVED")
        ]
        if incomplete_actions:
            blocking_reasons.append(
                f"{len(incomplete_actions)} remediation action(s) are still unresolved (status: {[a.get('status') for a in incomplete_actions]})."
            )

        # 3. Check for failed or blocked tests
        failed_tests = [
            t for t in test_executions
            if t.get("result") in ("FAILED", "BLOCKED")
        ]
        if failed_tests:
            blocking_reasons.append(
                f"{len(failed_tests)} test execution(s) are in FAILED or BLOCKED state."
            )

        # 4. Mandatory RETEST actions must have passing verification
        retest_results = [
            r for r in impact_results
            if r.get("disposition") == "RETEST_REQUIRED"
        ]
        passing_art_ids = {
            t.get("artifact_id") for t in test_executions if t.get("result") == "PASSED"
        }
        untested_retests = [
            r for r in retest_results
            if r.get("artifact_id") not in passing_art_ids
        ]
        if untested_retests:
            blocking_reasons.append(
                f"{len(untested_retests)} artifact(s) marked RETEST_REQUIRED do not have a passing test execution."
            )

        can_close = len(blocking_reasons) == 0
        return can_close, blocking_reasons
