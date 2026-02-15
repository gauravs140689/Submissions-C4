using FinSynth.Core;
using FinSynth.Core.Abstractions;
using FinSynth.Core.Models;
using System.Text.Json;

namespace FinSynth.Agents;

public class BudgetAdvisorAgent : GoogleGeminiAgentBase
{
    public override string AgentId => "budget-advisor";
    public override string Name => "Budget Optimization Specialist";
    public override string Specialty => "Analyzes spending patterns and creates actionable budget optimization plans";

    protected override string SystemPrompt => @"
You are a Budget Optimization Specialist with expertise in expense management and cash flow optimization.

Your responsibilities:
1. Analyze income and expense patterns
2. Identify opportunities to reduce non-essential spending
3. Recommend budget reallocation strategies
4. Create sustainable spending plans that align with financial goals

Analysis Framework:
- 50/30/20 Rule: 50% needs, 30% wants, 20% savings/debt
- Zero-based budgeting for maximum control
- Identify 'budget leaks' - small recurring expenses that add up
- Prioritize essential vs discretionary spending

Output Format:
- Current spending breakdown analysis
- Specific expense reduction recommendations
- Optimized budget allocation
- Monthly cash flow projection
- Actionable first steps

Be practical and non-judgmental. Focus on sustainable changes, not deprivation.
";

    public BudgetAdvisorAgent(string apiKey) : base(apiKey, "gemini-1.5-pro") { }

    protected override string BuildUserMessage(AgentRequest request)
    {
        if (!request.Context.TryGetValue("financial_snapshot", out var snapshotObj))
        {
            return base.BuildUserMessage(request);
        }

        var snapshot = JsonSerializer.Deserialize<FinancialSnapshot>(snapshotObj.ToString()!);
        if (snapshot == null) return base.BuildUserMessage(request);

        var totalIncome = snapshot.Incomes.Sum(i => i.MonthlyAmount);
        var totalExpenses = snapshot.Expenses.Sum(e => e.MonthlyAmount);
        var essentialExpenses = snapshot.Expenses.Where(e => e.IsEssential).Sum(e => e.MonthlyAmount);
        var discretionaryExpenses = snapshot.Expenses.Where(e => !e.IsEssential).Sum(e => e.MonthlyAmount);
        var totalDebtPayments = snapshot.Debts.Sum(d => d.MinimumPayment);
        var availableCashFlow = totalIncome - totalExpenses;

        var expenseBreakdown = string.Join("\n", snapshot.Expenses.Select(e =>
            $"- {e.Category}: ${e.MonthlyAmount:N2} ({(e.IsEssential ? "Essential" : "Discretionary")})"
        ));

        return $@"
User Question: {request.UserQuery}

INCOME:
- Total Monthly Income: ${totalIncome:N2}
{string.Join("\n", snapshot.Incomes.Select(i => $"  - {i.Source}: ${i.MonthlyAmount:N2}"))}

EXPENSES:
{expenseBreakdown}

EXPENSE SUMMARY:
- Essential Expenses: ${essentialExpenses:N2} ({essentialExpenses / totalIncome:P0} of income)
- Discretionary Expenses: ${discretionaryExpenses:N2} ({discretionaryExpenses / totalIncome:P0} of income)
- Total Expenses: ${totalExpenses:N2}
- Debt Payments: ${totalDebtPayments:N2}
- Available Cash Flow: ${availableCashFlow:N2}

Analyze this budget and provide specific, actionable optimization recommendations.
";
    }
}
