# INVESTMENT EXPERT SYSTEM

def investment_expert(profile: dict) -> dict:
    """
    Args:
      age               int
      risk_tolerance    'low' | 'medium' | 'high'
      duration          'Less than 1 year' | '1-3 years' |
                        '3-5 years' | 'More than 5 years'
      savings_rate      float  0.0–1.0
      expect            '10%-20%' | '20%-30%' | '30%-40%'
      objective         'Capital Appreciation' | 'Growth' | 'Income'
      savings_goal      'Retirement Plan' | 'Health Care' | 'Education' |
                        'Wealth Creation' | 'Savings for Future'
      has_emergency_fund bool
      has_debt           bool
      monthly_income    float (INR)

    Returns:
      dict with keys: recommendations, allocation, reasons, warnings
    """
    scores   = {"Equity": 0, "Mutual Fund": 0, "Fixed Deposits": 0,
                "Public Provident Fund": 0, "Gold": 0}
    reasons  = []
    warnings = []

    age      = profile["age"]
    risk     = profile["risk_tolerance"]
    duration = profile["duration"]
    sr       = profile["savings_rate"]
    expect   = profile["expect"]
    obj      = profile["objective"]
    goal     = profile["savings_goal"]
    emf      = profile["has_emergency_fund"]
    debt     = profile["has_debt"]

    # ── GATE 1: No emergency fund
    if not emf:
        warnings.append(
            "⚠️ No emergency fund detected. Build 3–6 months of expenses in "
            "FD / liquid savings BEFORE investing in market instruments."
        )
        scores["Fixed Deposits"] += 5

    # ── GATE 2: Active debt
    if debt:
        warnings.append(
            "⚠️ Active debt detected. Clear high-interest loans first — "
            "that's a guaranteed 18–24% 'return'."
        )
        for k in scores:
            scores[k] = int(scores[k] * 0.6)

    # ── RULE 1: Age band 
    if age < 25:
        scores["Equity"] += 4; scores["Mutual Fund"] += 3
        reasons.append(f"Age {age} (<25): Max time horizon → equity-heavy")
    elif age < 35:
        scores["Equity"] += 3; scores["Mutual Fund"] += 3
        scores["Public Provident Fund"] += 1
        reasons.append(f"Age {age} (25–34): Growth phase → equity + mutual funds core")
    elif age < 45:
        scores["Mutual Fund"] += 3; scores["Equity"] += 2
        scores["Public Provident Fund"] += 2; scores["Gold"] += 1
        reasons.append(f"Age {age} (35–44): Balance growth vs security")
    elif age < 55:
        scores["Fixed Deposits"] += 3; scores["Public Provident Fund"] += 3
        scores["Mutual Fund"] += 2; scores["Gold"] += 1
        reasons.append(f"Age {age} (45–54): Pre-retirement → capital preservation")
    else:
        scores["Fixed Deposits"] += 4; scores["Public Provident Fund"] += 3
        scores["Gold"] += 2
        reasons.append(f"Age {age} (55+): Safety first, regular income needed")

    # ── RULE 2: Risk tolerance 
    if risk == "high":
        scores["Equity"] += 4; scores["Mutual Fund"] += 2
        reasons.append("High risk → direct equity + equity mutual funds")
    elif risk == "low":
        scores["Fixed Deposits"] += 4; scores["Public Provident Fund"] += 3
        scores["Gold"] += 2
        reasons.append("Low risk → guaranteed-return instruments (FD, PPF, Gold)")
    else:
        scores["Mutual Fund"] += 3; scores["Public Provident Fund"] += 2
        scores["Gold"] += 1
        reasons.append("Medium risk → diversified mutual funds + PPF + gold")

    # ── RULE 3: Horizon 
    if "More than 5" in duration:
        scores["Equity"] += 3; scores["Public Provident Fund"] += 3
        scores["Mutual Fund"] += 2
        reasons.append("Horizon >5 yrs: compounding favours equity & PPF")
    elif "3-5" in duration:
        scores["Mutual Fund"] += 3; scores["Fixed Deposits"] += 1
        reasons.append("3–5 yr horizon: mutual funds ideal window")
    elif "1-3" in duration:
        scores["Fixed Deposits"] += 3; scores["Gold"] += 1
        reasons.append("1–3 yr horizon: FD + small gold allocation")
    else:
        scores["Fixed Deposits"] += 5
        reasons.append("Horizon <1 yr: liquid instruments only (FD / liquid fund)")

    # ── RULE 4: Return expectation
    if expect == "30%-40%":
        scores["Equity"] += 4; scores["Mutual Fund"] += 2
        reasons.append("30–40% target: only equity can potentially reach this")
    elif expect == "20%-30%":
        scores["Equity"] += 2; scores["Mutual Fund"] += 3
        reasons.append("20–30% target: equity mutual funds / mid-cap SIP")
    else:
        scores["Fixed Deposits"] += 2; scores["Public Provident Fund"] += 2
        scores["Gold"] += 1
        reasons.append("10–20% target: FD (~7%), PPF (~7.1%), Gold (~10%)")

    # ── RULE 5: Objective 
    if obj == "Capital Appreciation":
        scores["Equity"] += 3; scores["Mutual Fund"] += 2
        reasons.append("Objective: Capital Appreciation → equity instruments")
    elif obj == "Growth":
        scores["Mutual Fund"] += 3; scores["Equity"] += 1
        scores["Public Provident Fund"] += 1
        reasons.append("Objective: Growth → diversified mutual funds")
    else:
        scores["Fixed Deposits"] += 3; scores["Public Provident Fund"] += 2
        reasons.append("Objective: Income → FD (payouts) or PPF (maturity)")

    # ── RULE 6: Savings goal 
    if goal == "Retirement Plan":
        scores["Public Provident Fund"] += 4; scores["Equity"] += 1
        reasons.append("Goal: Retirement → PPF (15yr, tax-free, 80C benefit)")
    elif goal == "Health Care":
        scores["Fixed Deposits"] += 3; scores["Gold"] += 2
        reasons.append("Goal: Health Care → FD (liquid) + Gold (crisis hedge)")
    elif goal == "Education":
        scores["Mutual Fund"] += 3; scores["Public Provident Fund"] += 2
        reasons.append("Goal: Education → SIP in mutual fund + PPF corpus")
    elif goal == "Wealth Creation":
        scores["Equity"] += 3; scores["Mutual Fund"] += 2
        reasons.append("Goal: Wealth Creation → equity / MF compounding")
    else:
        scores["Fixed Deposits"] += 2; scores["Mutual Fund"] += 2
        reasons.append("Goal: Future Savings → balanced FD + mutual fund")

    # ── RULE 7: Savings rate
    if sr > 0.35:
        scores["Equity"] += 2; scores["Mutual Fund"] += 2
        reasons.append(f"Savings rate {sr*100:.0f}% (>35%) → can absorb volatility")
    elif sr < 0.15:
        scores["Fixed Deposits"] += 2
        reasons.append(f"Savings rate {sr*100:.0f}% (<15%) → prioritise safety")

    # ── Build allocation 
    total  = sum(scores.values())
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if total == 0:
        return {
            "recommendations": ["Fixed Deposits"],
            "allocation": {"Fixed Deposits": 100},
            "reasons": ["Insufficient data — defaulting to safest option"],
            "warnings": warnings,
        }

    allocation = {k: round(v / total * 100) for k, v in ranked if v > 0}
    diff = 100 - sum(allocation.values())
    if allocation:
        allocation[list(allocation.keys())[0]] += diff

    return {
        "recommendations": [k for k, v in ranked[:3] if v > 0],
        "allocation":       allocation,
        "reasons":          reasons,
        "warnings":         warnings,
    }
