import re
import json

_tokenizer   = None
_model_bert  = None
_device      = None
_id2label    = None

def _load_nlp_model():
    global _tokenizer, _model_bert, _device, _id2label

    if _tokenizer is not None:
        return True

    try:
        import torch
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
        from huggingface_hub import hf_hub_download

        MODEL_NAME = "abhijeet599/nlp-chatbot-model"

        _tokenizer  = DistilBertTokenizer.from_pretrained(MODEL_NAME)
        _model_bert = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME)

        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model_bert.to(_device)
        _model_bert.eval()

        file_path = hf_hub_download(
            repo_id=MODEL_NAME,
            filename="id2label.json"
        )

        with open(file_path) as f:
            _id2label = {int(k): v for k, v in json.load(f).items()}

        return True

    except Exception as e:
        print(f"[chatbot] NLP model load failed: {e}")
        return False

# SESSION PROFILE
def get_user_profile():
    import streamlit as st
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {
            "name":          "",
            "age":           20,
            "income":        0,
            "monthly_spent": 0,
            "necessary":     0,
            "leisure":       0,
            "savings":       0,
            "savings_rate":  0.0,
            "groceries":     0,
            "transport":     0,
            "entertainment": 0,
            "bills":         0,
            "health":        0,
            "shopping":      0,
            "misc":          0,
            "goals": [],
        }
    return st.session_state.user_profile


# NLP INTENT PREDICTION
def predict_intent_bert(text):
    if not _load_nlp_model():
        return "unknown", 0.0
    import torch
    inputs = _tokenizer(text, return_tensors="pt", truncation=True,
                        padding=True, max_length=64)
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = _model_bert(**inputs)
    probs      = torch.softmax(outputs.logits, dim=1)
    conf, pred = torch.max(probs, dim=1)
    return _id2label[pred.item()], conf.item()


# ENTITY EXTRACTION
def extract_amount(text: str) -> int:
    """
    Parse amounts from natural language including Indian shorthand.
    Examples:
      '40k'        → 40000
      '40K'        → 40000
      '1.5k'       → 1500
      '2 lakh'     → 200000
      '2.5 lakh'   → 250000
      '1 lakh 50'  → (150000 — handled via base + remainder)
      '10 cr'      → 10000000
      '1.5 crore'  → 15000000
      '500'        → 500
      '1,500'      → 1500
      '40,000'     → 40000
    """
    t = text.lower().strip()

    # Remove currency symbols
    t = t.replace("₹", "").replace("rs", "").replace("inr", "")

    # ── Pattern: number + multiplier word
    multipliers = [
        (r'(?:crore|cr)\b',       1_00_00_000),
        (r'(?:lakh|lac)\b',       1_00_000),
        (r'(?:thousand|k)\b',     1_000),
    ]

    # Try each multiplier from largest to smallest
    for pattern, factor in multipliers:
        m = re.search(
            r'(\d[\d,]*)(\.\d+)?\s*' + pattern,
            t
        )
        if m:
            integer_part = int(m.group(1).replace(",", ""))
            decimal_part = float(m.group(2)) if m.group(2) else 0.0
            base = (integer_part + decimal_part) * factor
            return int(base)

    # ── Pattern: plain number (with optional commas)
    m = re.search(r'\d[\d,]*', t)
    if m:
        return int(m.group().replace(",", ""))

    return 0


def extract_category(text: str) -> str:
    t = text.lower()
    rules = {
        "salary":        ["salary", "income", "earned", "credited",
                          "bonus", "paycheck", "stipend", "received", "pay"],
        "groceries":     ["grocer", "vegetable", "sabzi", "kirana",
                          "supermarket", "milk", "ration"],
        "food":          ["food", "eat", "lunch", "dinner", "breakfast",
                          "swiggy", "zomato", "snack", "coffee", "tea",
                          "restaurant", "cafe", "dining"],
        "travel":        ["travel", "bus", "train", "uber", "ola",
                          "petrol", "cab", "auto", "taxi", "fuel",
                          "metro", "flight", "hotel", "trip"],
        "entertainment": ["game", "gamepass", "netflix", "prime",
                          "hotstar", "movie", "fun", "concert",
                          "ott", "disney", "subscription"],
        "bills":         ["bill", "electricity", "water", "rent",
                          "recharge", "wifi", "internet", "gas",
                          "maintenance", "utility"],
        "shopping":      ["shop", "cloth", "dress", "shoes", "bag",
                          "amazon", "flipkart", "online", "fashion"],
        "health":        ["doctor", "hospital", "medicine", "medical",
                          "pharmacy", "clinic", "gym", "fitness"],
    }
    for cat, kws in rules.items():
        if any(kw in t for kw in kws):
            return cat
    return "misc"


# INVESTMENT RECOMMENDATION
def _derive_duration(age: int) -> str:
    if age < 30:  return "More than 5 years"
    if age < 40:  return "3-5 years"
    if age < 50:  return "3-5 years"
    return "1-3 years"


def _derive_expect(risk: str) -> str:
    return {"high": "30%-40%", "medium": "20%-30%", "low": "10%-20%"}[risk]


def build_expert_input(p: dict) -> dict:
    sr   = p.get("savings_rate", 0.0)
    age  = p.get("age", 30)
    risk = "high" if sr > 0.35 else ("medium" if sr > 0.20 else "low")
    return {
        "age":                age,
        "risk_tolerance":     risk,
        "duration":           _derive_duration(age),
        "savings_rate":       sr,
        "expect":             _derive_expect(risk),
        "objective":          ("Capital Appreciation" if risk == "high"
                               else "Growth" if risk == "medium" else "Income"),
        "savings_goal":       "Wealth Creation",
        "has_emergency_fund": sr > 0.10,
        "has_debt":           False,
        "monthly_income":     p.get("income", 0),
    }


def get_recommendation(p: dict) -> str:
    from investment_engine import investment_expert
    result = investment_expert(build_expert_input(p))

    inc      = p.get("income", 0)
    sr       = p.get("savings_rate", 0)
    savings  = p.get("savings", 0)
    age      = p.get("age", 30)
    name     = p.get("name", "")

    # Investable surplus = savings minus 3-month emergency fund buffer
    # Suggest deploying ~80% of monthly savings into investments
    investable = max(0, int(savings * 0.80))

    greeting = f"Sure {name}! " if name else "Sure! "

    lines = [
        f"{greeting}Based on your profile — age {age}, "
        f"₹{inc:,.0f}/mo income, {sr*100:.0f}% savings rate — "
        f"here's your personalised investment plan:\n"
    ]

    lines.append("**📊 Recommended Monthly Allocation**")
    lines.append(f"_(based on ₹{investable:,}/mo investable surplus)_\n")

    for avenue, pct in result["allocation"].items():
        amount = int(investable * pct / 100)
        lines.append(f"**{avenue}** — {pct}% → ₹{amount:,}/mo")

    lines.append("\n**💡 Why this plan:**")
    for r in result["reasons"][:4]:
        lines.append(f"→ {r}")

    if result["warnings"]:
        lines.append("\n**⚠️ Before investing, address this:**")
        for w in result["warnings"]:
            lines.append(f"{w}")

    lines.append(
        f"\n_Your full allocation breakdown is also on the **Visualization** page._"
    )

    return "\n".join(lines)



# CHATBOT RESPONSE POLISH — natural language wrappers
def _fmt_balance_response(p: dict) -> str:
    inc     = p.get("income", 0)
    spent   = p.get("monthly_spent", 0)
    savings = p.get("savings", 0)
    sr      = p.get("savings_rate", 0)
    name    = p.get("name", "")

    sr_label = "excellent 🔥" if sr > 0.35 else "healthy ✅" if sr > 0.20 else "a bit low ⚠️"
    tip = ""
    if sr < 0.20 and inc > 0:
        gap = int(inc * 0.20 - savings)
        tip = f"\n\nTo hit the recommended 20% savings rate, you'd need to cut ₹{gap:,}/mo from expenses."
    elif sr > 0.35:
        investable = int(savings * 0.80)
        tip = f"\n\nWith ₹{investable:,}/mo to invest, ask me *'where should I invest'* for a personalised plan."

    greeting = f"Here you go{', ' + name if name else ''}! " 
    return (
        f"{greeting}Your finances this month:\n\n"
        f"💰 **Savings**: ₹{savings:,.0f} ({sr*100:.1f}% of income) — {sr_label}\n"
        f"📤 **Spent**: ₹{spent:,.0f} out of ₹{inc:,.0f} income"
        f"{tip}"
    )


def _fmt_expense_response(p: dict) -> str:
    inc   = p.get("income", 0)
    spent = p.get("monthly_spent", 0)
    pct   = spent / inc * 100 if inc else 0
    left  = inc - spent
    label = "on track 👍" if pct < 70 else "getting high ⚠️" if pct < 90 else "over budget 🚨"

    return (
        f"You've spent **₹{spent:,.0f}** this month — "
        f"that's **{pct:.1f}%** of your ₹{inc:,.0f} income ({label}).\n\n"
        f"₹{left:,.0f} remaining for the rest of the month."
    )


def _fmt_income_response(p: dict) -> str:
    inc  = p.get("income", 0)
    sr   = p.get("savings_rate", 0)
    name = p.get("name", "")
    annual = inc * 12

    return (
        f"Your monthly income is **₹{inc:,.0f}** "
        f"(₹{annual:,.0f}/year{', ' + name if name else ''}).\n\n"
        f"You're currently saving **{sr*100:.1f}%** of that — "
        f"{'which is great! 🔥' if sr > 0.30 else 'aim for at least 20% for long-term wealth.'}"
    )


def _fmt_monthly_analysis(p: dict) -> str:
    inc     = p.get("income", 0)
    spent   = p.get("monthly_spent", 0)
    savings = p.get("savings", 0)
    sr      = p.get("savings_rate", 0)
    name    = p.get("name", "")

    # Spending health
    spent_pct = spent / inc * 100 if inc else 0
    if sr > 0.35:
        health_msg = "You're saving aggressively — excellent financial discipline! 🔥"
        action = f"Consider putting ₹{int(savings*0.8):,}/mo to work in equity SIPs."
    elif sr > 0.20:
        health_msg = "Your savings rate is healthy and above the 20% benchmark. ✅"
        action = "Keep it up — consistency compounds."
    elif sr > 0.10:
        health_msg = "You're saving something, but below the 20% recommended rate. ⚠️"
        gap = int(inc * 0.20 - savings)
        action = f"Try cutting ₹{gap:,}/mo from variable expenses to hit 20%."
    else:
        health_msg = "Savings rate is critically low — prioritise cutting expenses. 🚨"
        action = "Start with leisure spending — small cuts add up fast."

    cats = ["groceries", "food", "travel", "entertainment", "bills", "shopping", "health", "misc"]
    cat_lines = []
    for c in cats:
        v = p.get(c, 0)
        if v > 0:
            cat_lines.append(f"  • {c.title()}: ₹{v:,}")
    cat_section = ("\n\n**📂 Where it went:**\n" + "\n".join(cat_lines)) if cat_lines else ""

    greeting = f"Here's your monthly picture{', ' + name if name else ''}:\n\n"
    return (
        f"{greeting}"
        f"| | Amount |\n"
        f"|---|---|\n"
        f"| 📥 Income | ₹{inc:,.0f} |\n"
        f"| 📤 Spent  | ₹{spent:,.0f} ({spent_pct:.0f}%) |\n"
        f"| 💰 Saved  | ₹{savings:,.0f} ({sr*100:.1f}%) |\n\n"
        f"{health_msg}\n"
        f"**Next step:** {action}"
        f"{cat_section}"
    )


def _fmt_risk_response(p: dict) -> str:
    sr  = p.get("savings_rate", 0)
    age = p.get("age", 30)

    if sr > 0.35:
        profile = "**High risk tolerance** — your strong savings buffer can absorb volatility."
        options = (
            "• **Equity / Index funds** — highest long-term returns, 7-10 yr horizon\n"
            "• **Mid-cap SIP** — higher growth, moderate volatility\n"
            "• **Gold ETF** (~10%) — hedge against equity downturns"
        )
    elif sr > 0.20:
        profile = "**Medium risk tolerance** — balanced approach suits you."
        options = (
            "• **Flexi-cap mutual funds** — growth with professional management\n"
            "• **PPF** — guaranteed 7.1%, tax-free, 80C benefit\n"
            "• **FD** for short-term needs (1-3 yr)"
        )
    else:
        profile = "**Low risk tolerance** — safety first given your current savings rate."
        options = (
            "• **Fixed Deposits** — ~7% guaranteed, fully safe\n"
            "• **PPF** — 7.1%, government-backed, tax-free\n"
            "• **Recurring Deposits** — builds saving discipline"
        )

    age_note = ""
    if age < 30:
        age_note = f"\n\nAt age {age}, time is your biggest asset — even moderate equity exposure compounds powerfully."
    elif age > 50:
        age_note = f"\n\nAt age {age}, prioritise capital preservation over growth."

    return (
        f"{profile}\n\n"
        f"**Suitable options for you:**\n{options}"
        f"{age_note}\n\n"
        f"_Want a full personalised plan? Ask: 'where should I invest'_"
    )


def _find_goal_by_name(goals: list, query: str) -> tuple:
    """
    Find which goal the user is referring to. Returns (index, goal_dict) or (-1, None).
    Tries exact match first, then substring match, then first goal as fallback
    if only one goal exists.
    """
    q = query.lower()

    # Exact match
    for i, g in enumerate(goals):
        if g["name"].lower() == q.strip():
            return i, g

    # Substring match
    for i, g in enumerate(goals):
        if g["name"].lower() in q or q in g["name"].lower():
            return i, g

    # Single goal — assume that's the one
    if len(goals) == 1:
        return 0, goals[0]

    return -1, None


def _get_spending_cuts(p: dict) -> list:
    """
    Analyse actual tracked spending and return ranked cut suggestions
    with exact rupee amounts. Only suggests cuts on variable categories.
    """
    inc = p.get("income", 1)
    variable_rules = {
        "food":          ("Food & Dining",    0.15, 0.30,
                          "Cooking at home even 3 days a week cuts this significantly."),
        "entertainment": ("Entertainment",    0.08, 0.40,
                          "Audit subscriptions — OTT, gaming, music. Cancel ones you rarely use."),
        "shopping":      ("Shopping",         0.12, 0.35,
                          "Introduce a 48-hour rule before any non-essential purchase."),
        "misc":          ("Miscellaneous",    0.10, 0.30,
                          "Miscellaneous is usually impulse spending — track it for a week and you'll find the leak."),
        "travel":        ("Travel & Commute", 0.12, 0.25,
                          "Carpooling or public transport a few days a week adds up fast."),
        "health":        ("Health & Fitness", 0.08, 0.20,
                          "Check if you're paying for a gym you rarely visit."),
        "leisure":       ("Leisure",          0.15, 0.30,
                          "Leisure is the most flexible budget line — small consistent cuts compound fast."),
    }
    suggestions = []
    for cat, (display, threshold, cut_pct, reason) in variable_rules.items():
        current = p.get(cat, 0)
        if current <= 0:
            continue
        ratio = current / inc
        if ratio > threshold or current > 300:
            cut = int(current * cut_pct)
            new = current - cut
            suggestions.append({
                "category":   display,
                "current":    current,
                "cut":        cut,
                "new":        new,
                "pct_of_inc": ratio * 100,
                "reason":     reason,
            })
    suggestions.sort(key=lambda x: -x["cut"])
    return suggestions


def _fmt_spending_advice(p: dict, goal_amount: int = 0, goal_label: str = "") -> str:
    """
    Spending-aware savings advice. Uses real tracked data to give
    specific, named cuts with exact rupee amounts — never generic tips.
    """
    inc     = p.get("income", 0)
    savings = p.get("savings", 0)
    sr      = p.get("savings_rate", 0)
    name    = p.get("name", "")
    leisure = p.get("leisure", 0)

    if inc == 0:
        return "Set up your income on the **USER** page first so I can analyse your spending."

    greeting = f"Let's find some savings{(', ' + name) if name else ''}. 🔍\n\n"
    cuts = _get_spending_cuts(p)

    if not cuts and leisure > 0:
        cut = int(leisure * 0.30)
        cuts = [{
            "category":   "Leisure",
            "current":    leisure,
            "cut":        cut,
            "new":        leisure - cut,
            "pct_of_inc": leisure / inc * 100,
            "reason":     "Leisure is your most flexible budget line — a 30% trim is usually painless.",
        }]

    if not cuts:
        return (
            f"{greeting}I don't have enough spending data yet.\n\n"
            f"Add expenses through chat — e.g. *'spent 500 on food'*, *'paid 400 for entertainment'* "
            f"— and I'll pinpoint exactly where you can save."
        )

    total_cut   = sum(c["cut"] for c in cuts)
    new_savings = savings + total_cut
    new_sr      = new_savings / inc * 100 if inc else 0

    lines = [greeting]
    lines.append(f"You currently save **₹{savings:,}/mo ({sr*100:.0f}% of income)**.\n")

    if goal_amount > 0 and goal_label:
        months_now   = -(-goal_amount // savings) if savings > 0 else 999
        months_new   = -(-goal_amount // new_savings) if new_savings > 0 else 999
        saved_months = months_now - months_new
        lines.append(
            f"**Goal — {goal_label} (₹{goal_amount:,}):**\n"
            f"At current savings: **{months_now} months**\n"
            f"With cuts below: **{months_new} months** ({saved_months} months faster ⚡)\n"
        )

    lines.append("**Here's where to cut — specific amounts, not vague tips:**\n")

    for i, c in enumerate(cuts[:4], 1):
        cut_pct_label = int(c["cut"] / c["current"] * 100)
        lines.append(
            f"**{i}. {c['category']}** — currently ₹{c['current']:,}/mo ({c['pct_of_inc']:.0f}% of income)\n"
            f"   Trim by {cut_pct_label}% → save **₹{c['cut']:,}/mo**, new budget: ₹{c['new']:,}\n"
            f"   💡 _{c['reason']}_\n"
        )

    lines.append(
        f"**Total extra saving: ₹{total_cut:,}/mo**\n"
        f"New savings: **₹{new_savings:,}/mo ({new_sr:.0f}% rate)**"
    )
    if new_sr >= 30:
        lines.append(
            f"\nAt ₹{new_savings:,}/mo saved, ask *'where should I invest'* to put it to work."
        )
    return "\n".join(lines)


def _fmt_goal_response(p: dict) -> str:
    savings = p.get("savings", 0)
    name    = p.get("name", "")
    inc     = p.get("income", 0)

    greeting = f"Let's plan that goal{(', ' + name) if name else ''}! 🎯\n\n"

    if savings <= 0:
        if inc > 0:
            return (
                f"{greeting}You don't have positive monthly savings yet — let's fix that first.\n\n"
                + _fmt_spending_advice(p)
            )
        return (
            f"{greeting}Set up your income and expenses on the **USER** page "
            f"and I'll build you a personalised plan."
        )

    targets = [
        (50_000,    "New phone / gadget"),
        (1_00_000,  "Foreign trip"),
        (5_00_000,  "Car down payment"),
        (20_00_000, "Home down payment"),
    ]

    lines = [
        f"{greeting}With **₹{savings:,}/month** in savings, here's what you can reach:\n",
        "| Goal | Target | Months needed |",
        "|---|---|---|",
    ]
    for target, label in targets:
        months = -(-target // savings)
        years  = f" ({months//12}y {months%12}m)" if months > 12 else ""
        lines.append(f"| {label} | ₹{target:,} | {months} months{years} |")

    cuts = _get_spending_cuts(p)
    if cuts:
        total_cut   = sum(c["cut"] for c in cuts)
        new_savings = savings + total_cut
        lines.append(
            f"\n**Want to get there faster?**\n"
            f"Cut variable expenses → save **₹{new_savings:,}/mo** instead:\n"
        )
        for c in cuts[:3]:
            lines.append(
                f"  → Reduce **{c['category']}** ₹{c['current']:,} → "
                f"₹{c['new']:,} — saves **₹{c['cut']:,}/mo**"
            )
        lines.append(f"\nAsk *'how can I save more'* for the full breakdown.")

    lines.append(f"\n💡 Use the **Goal Tracking** page to set a target and track progress.")
    return "\n".join(lines)


# FINANCIAL TIPS (used by monthly analysis)
def financial_advice_tips(p: dict) -> str:
    sr    = p.get("savings_rate", 0)
    lines = []
    cuts  = _get_spending_cuts(p)
    if cuts and sr < 0.30:
        top = cuts[0]
        lines.append(
            f"💡 Top saving opportunity: cut **{top['category']}** by ₹{top['cut']:,}/mo. "
            f"Ask *'how can I save more'* for the full plan."
        )
    if sr < 0.20:
        lines.append("⚠️ Savings below 20% — focus on reducing variable spending.")
    elif sr > 0.35:
        lines.append("🔥 Excellent savings rate! Ask *'where should I invest'* to put it to work.")
    else:
        lines.append("✅ Savings rate is healthy. Keep it consistent.")
    return "\n".join(lines) if lines else "✅ Your finances look balanced. Keep it up!"

# MAIN CHATBOT
def chatbot(query: str) -> str:
    q = query.lower().strip()
    p = get_user_profile()

    # ── 1. Greeting / Goodbye 
    if re.search(r'\b(hi|hello|hey|namaste|howdy)\b', q):
        name = p.get("name", "")
        greet = f"Hello {name}! " if name else "Hello! "
        return (greet + "I'm your AI Financial Advisor 💰\n\n"
                "I can help you:\n"
                "  • Track expenses  → 'spent 500 on food'\n"
                "  • Check balance   → 'what is my balance'\n"
                "  • Get investment advice → 'where should I invest'\n"
                "  • Monthly report  → 'show monthly analysis'")

    if re.search(r'\b(bye|goodbye|exit|quit|done)\b', q):
        return "Goodbye! Stay financially fit! 👋"

    # ── 2. Add income 
    income_kws = ["salary", "income", "earned", "credited", "bonus",
                  "paycheck", "stipend", "received", "got paid"]
    if re.search(r'\d', q) and any(kw in q for kw in income_kws):
        amt = extract_amount(query)
        if amt > 0:
            p["income"]       += amt
            p["savings"]       = p["income"] - p["monthly_spent"]
            p["savings_rate"]  = p["savings"] / p["income"] if p["income"] else 0
            sr_pct = p["savings_rate"] * 100
            note = (f" Great savings rate of {sr_pct:.0f}%! 🔥" if sr_pct > 35
                    else f" You're saving {sr_pct:.0f}% of your income.")
            return (
                f"Got it! ₹{amt:,} income recorded. 💰\n\n"
                f"Monthly income is now **₹{p['income']:,.0f}**."
                f"{note}"
            )

    # ── 3. Add expense 
    # Skip if this looks like a goal contribution (handled in 4b below)
    _goal_words = ["goal", "target", "towards", "toward", "saving for",
                   "saved for", "add to", "put in", "contribute"]
    _is_goal_query = any(kw in q for kw in _goal_words)

    if (not _is_goal_query
            and re.search(r'\b(spent|paid|used|bought|add|record|log)\b', q)
            and re.search(r'\d', q)):
        amt = extract_amount(query)
        cat = extract_category(query)
        if amt > 0 and cat != "salary":
            p["monthly_spent"]  += amt
            p[cat]               = p.get(cat, 0) + amt
            p["savings"]         = p["income"] - p["monthly_spent"]
            p["savings_rate"]    = p["savings"] / p["income"] if p["income"] else 0
            inc = p["income"]
            spent_pct = p["monthly_spent"] / inc * 100 if inc else 0
            status = "👍" if spent_pct < 70 else "⚠️ getting high"
            return (
                f"Logged! ₹{amt:,} on **{cat}** added. {status}\n\n"
                f"Total spent this month: **₹{p['monthly_spent']:,.0f}** ({spent_pct:.0f}% of income)\n"
                f"Savings remaining: **₹{p['savings']:,.0f}**"
            )

    # ── 4a. Save more / reduce expenses keywords → spending advice ───────────
    # Phrase-level matches
    save_more_phrases = [
        "save more", "save money", "reduce expense", "cut expense",
        "spend less", "how to save", "help me save", "reduce spending",
        "how can i save", "ways to save", "lower my expense",
        "cut my spending", "where am i wasting", "where to cut",
        "too much spending", "spending too much", "overspending",
        "help reduce", "reduce my bill", "how to reduce", "cut down",
        "minimize expense", "control spending", "control expense",
        "trim my", "where should i cut", "what should i cut",
        "financial discipline", "spend wisely", "reduce my spending",
        "cutting spending", "financial tips", "money tips", "budget tips",
        "save on expenses", "lower expenses",
    ]
    # Word-combination matches (e.g. "reduce my expenses", "cut those expenses")
    _qwords = set(q.split())
    _cut_words    = {"reduce", "cut", "lower", "trim", "minimize", "decrease", "limit"}
    _spend_words  = {"expense", "expenses", "spending", "spend", "outgoing", "outgoings"}
    _is_cut_query = bool(_cut_words & _qwords and _spend_words & _qwords)

    if any(ph in q for ph in save_more_phrases) or _is_cut_query:
        return _fmt_spending_advice(p)

    _has_number = bool(re.search(r'\d', q))

    if _is_goal_query and _has_number:
        goals = p.get("goals", [])
        if not goals:
            return (
                "You don't have any goals set up yet! "
                "Go to the **Goal Tracking** page to create one, "
                "then you can add money towards it here."
            )
        amt = extract_amount(query)
        if amt <= 0:
            return "I couldn't read the amount — try something like *'add 5k to bike goal'*."

        idx, goal = _find_goal_by_name(goals, query)
        if idx == -1:
            names = ", ".join(f"*{g['name']}*" for g in goals)
            return (
                f"I found {len(goals)} goals ({names}) but couldn't tell which one you mean. "
                f"Try: *'add 2000 to [goal name]'*."
            )

        # Apply contribution
        import streamlit as _st
        remaining_before = goal["target"] - goal.get("saved", 0)
        _st.session_state.user_profile["goals"][idx]["saved"] = (
            goal.get("saved", 0) + amt
        )
        new_saved    = _st.session_state.user_profile["goals"][idx]["saved"]
        target       = goal["target"]
        pct          = min(int(new_saved / target * 100), 100)
        remaining    = max(0, target - new_saved)
        done         = new_saved >= target

        if done:
            return (
                f"🎉 **Goal complete!** You've fully funded your *{goal['name']}* goal!\n\n"
                f"₹{new_saved:,} saved out of ₹{target:,} target. "
                f"Head to **Goal Tracking** to celebrate or set a new goal."
            )

        bar = f"{pct}% complete"
        return (
            f"✅ ₹{amt:,} added to **{goal['name']}**!\n\n"
            f"**{bar}** — ₹{new_saved:,} saved of ₹{target:,} target\n"
            f"Still needed : ₹{remaining:,}"
            + (f"\nAt your current savings rate you'll hit this in "
               f"**{-(-remaining // p['savings'])} months**." if p.get("savings", 0) > 0 else "")
        )

    # ── 4c. Investment keywords → expert engine
    if re.search(r'\b(invest|investment|portfolio|sip|mutual\s*fund|where\s*to\s*put)\b', q):
        if p["income"] == 0:
            return ("⚠️ Please set up your profile first (income + expenses) so I can "
                    "give you accurate investment advice. Go to the **USER** page.")
        return get_recommendation(p)

    # ── 5. BERT intent prediction 
    intent, conf = predict_intent_bert(query)

    if conf < 0.30:
        return ("I didn't quite catch that. Try:\n"
                "  • 'show my total expenses'\n"
                "  • 'check my balance'\n"
                "  • 'give me investment advice'\n"
                "  • 'spent 500 on food'")

    # ── 6. All 13 intent handlers
    if intent == "greeting":
        return chatbot("hi")        # reuse greeting handler

    elif intent == "goodbye":
        return "Goodbye! Stay financially fit! 👋"

    elif intent == "check_income":
        return _fmt_income_response(p)

    elif intent == "check_total_expense":
        return _fmt_expense_response(p)

    elif intent == "check_balance":
        return _fmt_balance_response(p)

    elif intent == "monthly_analysis":
        return _fmt_monthly_analysis(p)

    elif intent == "category_expense":
        cats = ["groceries", "food", "travel", "entertainment",
                "bills", "shopping", "health", "misc"]
        tracked = {c: p.get(c, 0) for c in cats if p.get(c, 0) > 0}
        total_tracked = sum(tracked.values())
        if not tracked:
            return (
                "I don't have any detailed category data yet. "
                "Add expenses by saying things like *'spent 500 on food'* "
                "and I'll track each category for you."
            )
        lines = [f"Here's where your ₹{total_tracked:,} tracked spend went:\n"]
        for c, v in sorted(tracked.items(), key=lambda x: -x[1]):
            pct = v / total_tracked * 100
            bar = "█" * int(pct // 8)
            lines.append(f"**{c.title()}** {bar} ₹{v:,} ({pct:.0f}%)")
        inc = p.get("income", 0)
        if inc > 0:
            pct_of_inc = total_tracked / inc * 100
            lines.append(f"\nTotal tracked: **{pct_of_inc:.0f}%** of your ₹{inc:,} income.")
        return "\n".join(lines)

    elif intent == "add_expense":
        return (
            "To log an expense, just tell me naturally:\n"
            "• *'spent 500 on food'*\n"
            "• *'paid 1200 for rent'*\n"
            "• *'bought shoes for 2000'*\n\n"
            "I'll categorise it and update your totals automatically."
        )

    elif intent == "add_income":
        return (
            "To record income, say:\n"
            "• *'salary credited 50000'*\n"
            "• *'earned bonus 10000'*\n"
            "• *'received freelance income 8000'*"
        )

    elif intent in ("investment_advice", "investment_recommendation_ml"):
        return get_recommendation(p)

    elif intent == "risk_assessment":
        return _fmt_risk_response(p)

    elif intent == "goal_setting":
        return _fmt_goal_response(p)

    elif intent == "spending_tips":
        return _fmt_spending_advice(p)

    return ("I can help with:\n"
            "  • Tracking expenses & income\n"
            "  • Checking balance & savings rate\n"
            "  • Investment advice\n"
            "  • Monthly analysis & goal planning\n"
            "  • Saving tips → try *'how can I save more'*")
