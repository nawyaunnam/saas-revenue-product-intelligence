"""Deterministic synthetic fixtures with churn, reactivation, expansion and late events."""

import random
from datetime import date, datetime, timedelta


def month_add(d, n):
    year, month = divmod(d.year * 12 + d.month - 1 + n, 12)
    return date(year, month + 1, 1)


def generate(accounts=120, months=18, seed=42):
    if accounts < 10 or not 3 <= months <= 36:
        raise ValueError("Use at least 10 accounts and 3–36 months")
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    end = month_add(start, months)
    data = {k: [] for k in ["accounts", "users", "subscriptions", "events", "opportunities", "marketing"]}
    eid = 0
    for i in range(accounts):
        aid = f"A{i:04d}"
        offset = rng.randrange(max(1, months - 2))
        signup = month_add(start, offset) + timedelta(days=rng.randrange(20))
        paid = signup + timedelta(days=rng.randrange(3, 22)) if i % 5 != 0 else None
        segment = ["SMB", "Mid-market", "Enterprise"][i % 3]
        data["accounts"].append(
            dict(
                account_id=aid,
                signup_date=signup,
                segment=segment,
                region=["AMER", "EMEA", "APAC"][i % 3],
                channel=["organic", "paid_search", "partner", "content"][i % 4],
            )
        )
        qualified = signup + timedelta(days=2) if i % 7 != 0 or paid else None
        data["opportunities"].append(
            dict(account_id=aid, trial_date=signup, qualified_date=qualified, paid_date=paid)
        )
        annual = i % 4 == 0
        base = [9900, 39900, 149900][i % 3]
        alive = True
        for m in range(offset, months):
            month = month_add(start, m)
            month_end = month_add(start, m + 1) - timedelta(days=1)
            age = m - offset
            # Explicit churn and reactivation, plus upgrades/downgrades.
            if age == 4 and i % 6 == 0:
                alive = False
            if age == 7 and i % 12 == 0:
                alive = True
            amount = base + (base // 2 if age >= 3 and i % 4 == 1 else 0)
            amount -= base // 4 if age >= 5 and i % 7 == 2 else 0
            amount = amount if paid and paid <= month_end and alive else 0
            data["subscriptions"].append(
                dict(
                    account_id=aid,
                    month=month,
                    amount_cents=amount * (12 if annual else 1),
                    billing_period="annual" if annual else "monthly",
                    plan=["Starter", "Growth", "Scale"][i % 3],
                )
            )
        for u in range(2 + i % 4):
            uid = f"{aid}U{u}"
            data["users"].append(dict(user_id=uid, account_id=aid, created_date=signup))
            d = signup
            while d < end:
                age = (d.year - signup.year) * 12 + d.month - signup.month
                churned = age >= 4 and i % 6 == 0 and not (age >= 7 and i % 12 == 0)
                if not churned and rng.random() < (0.15 + (i % 5) * 0.07):
                    names = ["login", rng.choice(["report_created", "export", "automation", "invite_sent"])]
                    if d <= signup + timedelta(days=6):
                        names.append("workspace_created")
                    for name in names:
                        eid += 1
                        ts = datetime.combine(d, datetime.min.time()) + timedelta(hours=10 + u)
                        event = dict(
                            event_id=f"E{eid:08d}",
                            user_id=uid,
                            account_id=aid,
                            occurred_at=ts,
                            event_name=name,
                            ingested_at=ts + timedelta(hours=1),
                        )
                        data["events"].append(event)
                        if eid % 97 == 0:  # CDC duplicate; newest arrival wins.
                            data["events"].append({**event, "ingested_at": ts + timedelta(days=2)})
                d += timedelta(days=1)
    d = start
    while d < end:
        for channel, spend in [
            ("organic", 5000),
            ("paid_search", 45000),
            ("partner", 12000),
            ("content", 18000),
        ]:
            data["marketing"].append(
                dict(spend_date=d, channel=channel, spend_cents=spend + rng.randrange(1000))
            )
        d += timedelta(days=1)
    return data
