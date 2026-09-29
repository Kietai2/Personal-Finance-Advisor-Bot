import os
import json
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "Disclaimer: This analysis and its recommendations are provided for informational and "
    "educational purposes only. Antigravity Personal Finance Advisor Bot does not provide certified "
    "legal, tax, or investment advice. Always consult a qualified financial professional before "
    "making major investment or financial commitments."
)

class GeminiService:
    @classmethod
    def get_api_key(cls):
        return current_app.config.get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY', '').strip()

    @classmethod
    def is_configured(cls):
        key = cls.get_api_key()
        return bool(key and key != 'your_gemini_api_key_here')

    @classmethod
    def analyze_finances(cls, financial_data, custom_query=None):
        """
        Analyzes structured financial data using Google Gemini API.
        Falls back to rule-based financial analysis if API key is missing or call fails.
        """
        if cls.is_configured():
            try:
                return cls._call_gemini_api(financial_data, custom_query)
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to local advisor engine: {e}")
                fallback = cls._generate_heuristic_advice(financial_data, custom_query)
                fallback['notice'] = f"Notice: Live Gemini API request encountered an issue ({str(e)}). Displaying tailored financial analysis from the built-in Intelligent Heuristics Engine."
                return fallback
        else:
            return cls._generate_heuristic_advice(financial_data, custom_query)

    @classmethod
    def _build_prompt(cls, financial_data, custom_query=None):
        summary = financial_data.get('summary', {})
        goals = financial_data.get('goals', [])
        budget_items = financial_data.get('budget_items', [])
        history = financial_data.get('history', [])
        
        prompt = f"""
You are the AI Financial Advisor for "Personal Finance Advisor Bot", a personal budgeting and financial planning assistant.
Analyze the user's financial profile below and provide actionable, encouraging, and balanced financial insights.

=== USER FINANCIAL PROFILE (Currency: Indian Rupee ₹) ===
Target Month: {summary.get('month_name', '')} {summary.get('year', '')}
Monthly Income: ₹{summary.get('total_income', 0):,.2f}
Total Expenses: ₹{summary.get('total_expenses', 0):,.2f}
Net Savings: ₹{summary.get('savings', 0):,.2f}
Savings Rate: {summary.get('savings_rate', 0):.1f}%
Total Budget Allocated: ₹{summary.get('total_budget', 0):,.2f}
Remaining Unspent Budget: ₹{summary.get('remaining_budget', 0):,.2f}

Category-wise Expenses:
{json.dumps(summary.get('category_breakdown', []), indent=2)}

Budget vs Actual Spending:
{json.dumps(budget_items, indent=2)}

Previous Month Comparison:
- Previous Month Income: ₹{summary.get('comparison', {}).get('prev_income', 0):,.2f}
- Previous Month Expenses: ₹{summary.get('comparison', {}).get('prev_expenses', 0):,.2f}
- Income Change: {summary.get('comparison', {}).get('income_change_pct', 0)}%
- Expenses Change: {summary.get('comparison', {}).get('expense_change_pct', 0)}%

Active Savings Goals:
{json.dumps([g.to_dict() if hasattr(g, 'to_dict') else g for g in goals], indent=2)}

Recent Monthly History:
{json.dumps(history, indent=2)}

User's Specific Question / Focus (if any):
{custom_query or "Provide a comprehensive, high-value monthly financial audit and recommendations."}

=== STRICT INSTRUCTIONS ===
Format your response cleanly in GitHub-flavored Markdown with these 6 clear sections:
### 1. Spending Observations
### 2. High-Spending Categories
### 3. Practical Ways to Reduce Unnecessary Spending
### 4. Suggestions for Improving Savings
### 5. Budgeting Recommendations
### 6. Goal Progress Observations

COMPLIANCE & SAFETY RULES:
- Use Indian Rupee (₹) for all figures.
- Do NOT pretend to be a licensed financial planner or certified financial analyst.
- Do NOT guarantee investment returns or promise that any scheme or stock will make money.
- Do NOT state speculative predictions as certain facts.
- Focus on budgeting, expense containment, cash flow management, emergency fund building, and goal planning.
- At the end, include the exact educational disclaimer:
"{DISCLAIMER_TEXT}"
"""
        return prompt

    @classmethod
    def _call_gemini_api(cls, financial_data, custom_query=None):
        api_key = cls.get_api_key()
        prompt = cls._build_prompt(financial_data, custom_query)
        
        # Try using google-genai SDK first
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            # Try gemini-1.5-flash or gemini-2.5-flash
            model_name = current_app.config.get('GEMINI_MODEL', 'gemini-1.5-flash')
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return {
                    'source': 'Gemini AI (Official SDK)',
                    'model': model_name,
                    'analysis': response.text,
                    'disclaimer': DISCLAIMER_TEXT,
                    'success': True
                }
        except Exception as sdk_err:
            logger.info(f"GenAI SDK attempt note: {sdk_err}. Trying direct REST API endpoint...")

        # Direct REST API Fallback to Generative Language API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get('candidates', [])
            if candidates:
                text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                return {
                    'source': 'Gemini AI (REST API)',
                    'model': 'gemini-1.5-flash',
                    'analysis': text,
                    'disclaimer': DISCLAIMER_TEXT,
                    'success': True
                }
        raise RuntimeError(f"Gemini API returned status {res.status_code}: {res.text}")

    @classmethod
    def _generate_heuristic_advice(cls, financial_data, custom_query=None):
        """
        Deterministic, intelligent rule-based financial reasoning engine.
        Ensures the application delivers complete, high-quality, actionable insights
        even when offline, without an API key, or if API quotas are exhausted.
        """
        summary = financial_data.get('summary', {})
        goals = financial_data.get('goals', [])
        budget_items = financial_data.get('budget_items', [])
        
        income = summary.get('total_income', 0.0)
        expenses = summary.get('total_expenses', 0.0)
        savings = summary.get('savings', 0.0)
        savings_rate = summary.get('savings_rate', 0.0)
        breakdown = summary.get('category_breakdown', [])
        comparison = summary.get('comparison', {})
        
        # 1. Spending Observations
        obs_lines = []
        if income > 0:
            obs_lines.append(f"- **Cash Flow Balance**: You recorded ₹{income:,.2f} in income and ₹{expenses:,.2f} in total expenses, generating a net monthly surplus of ₹{savings:,.2f}.")
            if savings_rate >= 20.0:
                obs_lines.append(f"- **Solid Savings Rate**: Your current savings rate of **{savings_rate:.1f}%** comfortably satisfies the recommended 20% benchmark from the standard 50/30/20 personal finance framework.")
            elif savings_rate > 0:
                obs_lines.append(f"- **Moderate Savings Rate**: Your savings rate is **{savings_rate:.1f}%**. Increasing this slightly toward 20% will build a sturdier cushion for unexpected life events.")
            else:
                obs_lines.append(f"- **Deficit Alert**: Your expenses currently match or exceed your income. Immediate prioritization of essential vs non-essential spending is recommended.")
        else:
            obs_lines.append("- **No Income Recorded**: There are no recorded income transactions for this period. Add your salary or other inflows to view a full cash-flow analysis.")

        if comparison.get('prev_expenses', 0) > 0:
            exp_chg = comparison.get('expense_change_pct', 0)
            if exp_chg > 5:
                obs_lines.append(f"- **Month-over-Month Shift**: Spending increased by **+{exp_chg}%** compared to the previous month (₹{comparison.get('prev_expenses', 0):,.2f}).")
            elif exp_chg < -5:
                obs_lines.append(f"- **Expense Reduction**: Excellent discipline! Spending decreased by **{exp_chg}%** compared to the prior month.")
            else:
                obs_lines.append("- **Stable Trajectory**: Overall spending remains consistent with your previous month's baseline.")

        # 2. High-Spending Categories
        high_cat_lines = []
        over_budget_cats = [b for b in budget_items if b.get('is_over_budget')]
        warning_budget_cats = [b for b in budget_items if b.get('status') == 'warning']

        if breakdown:
            top_cat = breakdown[0]
            high_cat_lines.append(f"- **Primary Expense Category**: **{top_cat['category']}** accounts for **₹{top_cat['amount']:,.2f}** ({top_cat['percentage']}% of all expenses).")
            if len(breakdown) > 1:
                second_cat = breakdown[1]
                high_cat_lines.append(f"- **Secondary Expense Category**: **{second_cat['category']}** represents **₹{second_cat['amount']:,.2f}** ({second_cat['percentage']}%).")
        else:
            high_cat_lines.append("- No expense categories logged yet for this billing cycle.")

        if over_budget_cats:
            for ob in over_budget_cats:
                high_cat_lines.append(f"- ⚠️ **Over Budget**: **{ob['category']}** reached ₹{ob['spent']:,.2f} against a planned budget of ₹{ob['budget']:,.2f} ({ob['percentage_used']}% utilized).")
        elif warning_budget_cats:
            for wb in warning_budget_cats:
                high_cat_lines.append(f"- 🔔 **Near Capacity**: **{wb['category']}** has utilized {wb['percentage_used']}% of its budget limit.")
        else:
            high_cat_lines.append("- **Budget Discipline**: None of your established category limits have been exceeded this month.")

        # 3. Practical Ways to Reduce Unnecessary Spending
        reduc_lines = [
            "- **Audit Discretionary Expenses**: Review food delivery apps and entertainment subscriptions. Cooking bulk weekend meals and consolidating streaming plans often yields immediate ₹1,500 - ₹3,000 monthly savings.",
            "- **The 48-Hour Purchase Pause**: For non-essential shopping items exceeding ₹1,500, enforce a 48-hour cooling period to curb impulse spending.",
            "- **Smart Transport & Utility Efficiency**: Recharge public transit passes in monthly bulk to capture commuter discounts, and unplug idle electronics to trim utility costs."
        ]

        # 4. Suggestions for Improving Savings
        savings_lines = [
            "- **Automate 'Pay-Yourself-First'**: On the date your salary is credited, transfer 15-20% immediately into a designated savings or liquid fund account before disbursing daily expenses.",
            "- **Maintain a Liquid Emergency Fund**: Prioritize establishing 3 to 6 months of basic living expenses (approx. ₹60,000 - ₹1,20,000) in a high-interest savings account or safe liquid instruments."
        ]

        # 5. Budgeting Recommendations
        budget_lines = [
            "- **Adopt the 50/30/20 Principle**: Allocate 50% of your take-home pay to essential needs (Rent, Groceries, Utilities, Bills), 30% to personal wants, and reserve 20% strictly for savings and goal funding.",
            "- **Dynamic Zero-Based Allocation**: Revisit your category allowances on the 1st of every month using the Automatic Budget Generator in the Budgets section."
        ]

        # 6. Goal Progress Observations
        goal_lines = []
        if goals:
            for g in goals:
                g_dict = g.to_dict() if hasattr(g, 'to_dict') else g
                name = g_dict.get('name', 'Goal')
                cur = g_dict.get('current_amount', 0)
                tar = g_dict.get('target_amount', 1)
                pct = g_dict.get('progress_percentage', 0)
                rem = g_dict.get('remaining_amount', 0)
                target_date = g_dict.get('target_date', 'Target')
                
                status_icon = "🎯" if pct >= 100 else ("⚡" if pct >= 50 else "🌱")
                goal_lines.append(f"- {status_icon} **{name}**: Progress is at **{pct}%** (₹{cur:,.2f} of ₹{tar:,.2f}). Remaining balance to save: ₹{rem:,.2f} by {target_date}.")
        else:
            goal_lines.append("- No financial goals created yet. Visit the **Savings Goals** tab to set targets such as an Emergency Fund, Tech Upgrade, or Higher Education.")

        content = f"""### 1. Spending Observations
{chr(10).join(obs_lines)}

### 2. High-Spending Categories
{chr(10).join(high_cat_lines)}

### 3. Practical Ways to Reduce Unnecessary Spending
{chr(10).join(reduc_lines)}

### 4. Suggestions for Improving Savings
{chr(10).join(savings_lines)}

### 5. Budgeting Recommendations
{chr(10).join(budget_lines)}

### 6. Goal Progress Observations
{chr(10).join(goal_lines)}

---
> 💡 *{DISCLAIMER_TEXT}*
"""
        return {
            'source': 'Built-in Financial Intelligence Heuristics Engine',
            'model': 'Rule-Based Deterministic Engine',
            'analysis': content,
            'disclaimer': DISCLAIMER_TEXT,
            'success': True,
            'notice': 'Notice: Running on built-in Financial Intelligence Heuristics Engine. To connect live Google Gemini AI, add your GEMINI_API_KEY in the `.env` file.'
        }
