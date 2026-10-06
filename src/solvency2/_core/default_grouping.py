"""Article190 equivalence classes on externally qualified relationships."""
from typing import Mapping

from .core import Context, calculation, exact_keys, require
from .default import _evidence
from .loss_given_default import _known_flag


def _identifier(value, field, *, nullable=False):
    require((nullable and value is None) or (isinstance(value, str) and bool(value.strip())),
            field, "nonempty string ID or explicitly qualified absence required")
    return value


@calculation("DR:article-190:1", "DR:article-190:2", unit="single_names")
def default_single_name_count(exposures: Mapping, *, pool_treatment: Mapping,
                              grouping_reference: str, context: Context,
                              provider_substitutions: Mapping | None = None):
    """Count declared single names and retain every exposure-to-group assignment.

    None for group/pool means externally established absence, NOT unknown.
    Pool separation suppresses the pool edge only, not the corporate-group
    rule. Optional189(5) substitutions are an explicit election, restricted to
    this count. Original/effective legal memberships and completeness of the
    relevant portfolio are external qualifications, never inferred from IDs.
    """
    _evidence(grouping_reference, "grouping_reference")
    require(isinstance(exposures, Mapping), "exposures", "labelled exposure mapping required")
    require(bool(exposures), "exposures", "explicit nonempty exposure set required", "MISSING_INPUT")
    rows, parties, pool_ids = {}, {}, set()
    for label, row in exposures.items():
        _identifier(label, "exposure_id")
        exact_keys(row, ("counterparty_id", "group_id", "pool_id"), label)
        party = _identifier(row["counterparty_id"], label + ".counterparty_id")
        group = _identifier(row["group_id"], label + ".group_id", nullable=True)
        pool = _identifier(row["pool_id"], label + ".pool_id", nullable=True)
        if party in parties:
            require(parties[party] == group, label + ".group_id",
                    "same counterparty has conflicting group declarations", "REVIEW_REQUIRED")
        parties[party] = group
        if pool is not None:
            pool_ids.add(pool)
        rows[label] = {"counterparty_id": party, "group_id": group, "pool_id": pool}

    original_rows = {label: dict(row) for label, row in rows.items()}
    substitutions = {}
    if provider_substitutions is not None:
        require(isinstance(provider_substitutions, Mapping), "provider_substitutions",
                "explicit mapping of elected exposure substitutions required")
        require(set(provider_substitutions) <= set(rows), "provider_substitutions",
                "provider election refers to unknown exposure")
        for label, protection in provider_substitutions.items():
            field = "provider_substitutions." + label
            exact_keys(protection, ("provider_id", "group_id", "pool_id", "full_protection",
                                   "mitigation_qualified", "qualification_reference"), field)
            provider = _identifier(protection["provider_id"], field + ".provider_id")
            group = _identifier(protection["group_id"], field + ".group_id", nullable=True)
            pool = _identifier(protection["pool_id"], field + ".pool_id", nullable=True)
            _evidence(protection["qualification_reference"], field + ".qualification_reference")
            full = _known_flag(protection["full_protection"], field + ".full_protection")
            qualified = _known_flag(protection["mitigation_qualified"], field + ".mitigation_qualified")
            require(full and qualified, field, "full qualifying209–215 protection required",
                    "REVIEW_REQUIRED")
            rows[label] = {"counterparty_id": provider, "group_id": group, "pool_id": pool}
            substitutions[label] = dict(protection)

    # Validate the effective parties again: distinct original counterparties can
    # become the same provider, including a party already present in the book.
    parties, pool_ids = {}, set()
    for label, row in rows.items():
        party, group, pool = row["counterparty_id"], row["group_id"], row["pool_id"]
        if party in parties:
            require(parties[party] == group, label + ".group_id",
                    "same effective counterparty has conflicting group declarations", "REVIEW_REQUIRED")
        parties[party] = group
        if pool is not None:
            pool_ids.add(pool)
    exact_keys(pool_treatment, pool_ids, "pool_treatment")
    policies = {}
    for pool in sorted(pool_ids):
        policy = pool_treatment[pool]
        exact_keys(policy, ("separate_members", "pd_lgd_qualified"), "pool." + pool)
        separate, qualified = policy["separate_members"], policy["pd_lgd_qualified"]
        require(separate is not None, "pool." + pool + ".separate_members",
                "pool separation choice must be known", "REVIEW_REQUIRED")
        require(isinstance(separate, bool), "pool." + pool + ".separate_members", "explicit boolean required")
        require(qualified is None or isinstance(qualified, bool), "pool." + pool + ".pd_lgd_qualified",
                "boolean qualification or unknown None required")
        require(not separate or qualified is True, "pool." + pool,
                "separation requires declared Article199 PD and type-specific193/194/195 LGD",
                "REVIEW_REQUIRED")
        policies[pool] = dict(policy)

    # Union-find preserves simultaneous, transitive party/group/pool relations.
    # The key namespaces are deliberately distinct, even when labels coincide.
    parent = {label: label for label in rows}

    def find(label):
        while parent[label] != label:
            parent[label] = parent[parent[label]]
            label = parent[label]
        return label

    def union(a, b):
        left, right = sorted((find(a), find(b)))
        parent[right] = left

    representatives = {}
    for label in sorted(rows):
        row = rows[label]
        keys = [("party", row["counterparty_id"])]
        if row["group_id"] is not None:
            keys.append(("group", row["group_id"]))
        pool = row["pool_id"]
        if pool is not None and not policies[pool]["separate_members"]:
            keys.append(("pool", pool))
        for key in keys:
            if key in representatives:
                union(label, representatives[key])
            else:
                representatives[key] = label
    groups = {}
    assignment = {}
    for label in sorted(rows):
        root = find(label)
        groups.setdefault(root, []).append(label)
        assignment[label] = root
    return len(groups), {
        "single_names": groups, "exposure_to_single_name": assignment,
        "exposures": {label: rows[label] for label in sorted(rows)},
        "original_exposures": {label: original_rows[label] for label in sorted(original_rows)},
        "provider_substitutions": {label: substitutions[label] for label in sorted(substitutions)},
        "pool_treatment": policies, "grouping_reference": grouping_reference,
        "membership_status": "EXTERNAL_UNVERIFIED", "portfolio_completeness_verified": False,
        "pool_pd_lgd_compliance_verified": False,
        "provider_substitution_performed": bool(substitutions),
        "provider_qualification_verified": False, "pd_or_lgd_substitution_performed": False,
        "capital_charge_computed": False,
        "scope": ("declared_article189_5_substitution_then190_count_only" if substitutions else
                  "declared_article190_relationships_only_no_189_5_substitution"),
        "_sources": ["DR:article-189:5"] if substitutions else []}
