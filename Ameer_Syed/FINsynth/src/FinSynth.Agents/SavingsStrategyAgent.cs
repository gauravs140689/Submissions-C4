using FinSynth.Core;
using FinSynth.Core.Abstractions;
using FinSynth.Core.Models;
using System.Text.Json;

namespace FinSynth.Agents;

public class SavingsStrategyAgent : GoogleGeminiAgentBase
{
    public override string AgentId => "savings-strategy";
    public override string Name => "Savings Strategy Specialist";
    public override string Specialty => "Creates personalized savings plans and financial goal strategies";

    protected override string SystemPrompt => @"
You are a Savings Strategy Specialist with expertise in personal finance and wealth building.

Your responsibilities:
1. Assess current savings position and emergency fund status
2. Create achievable savings goals based on income and expenses
3. Recommend optimal savings allocation strategies
4. Balance short-term and long-term financial objectives

Strategy Framework:
- Emergency Fund: 3-6 months expenses (priority #1)
- Short-term Goals: <2 years (high-yield savings, CDs)
- Medium-term Goals: 2-5 years (balanced approach)
- Long-term Goals: 5+ years (investment focus)

Output Format:
- Current savings health assessment
- Recommended monthly savings amount
- Goal-specific allocation breakdown
- Timeline to achieve each goal
- Automation recommendations

Be practical, encouraging, and actionable. Account for real-world constraints.
";

    public SavingsStrategyAgent(string apiKey) : base(apiKey, "gemini-1.5-pro") { }

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
        var totalDebtPayments = snapshot.Debts.Sum(d => d.MinimumPayment);
        var availableCashFlow = totalIncome - totalExpenses;
        var essentialExpenses = snapshot.Expenses.Where(e => e.IsEssential).Sum(e => e.MonthlyAmount);
        var emergencyFundMonths = snapshot.SavingsBalance / essentialExpenses;

        return $@"
User Question: {request.UserQuery}

CURRENT SAVINGS:
- Savings Balance: ${snapshot.SavingsBalance:N2}
- Emergency Fund Goal: ${snapshot.EmergencyFundGoal:N2}
- Current Coverage: {emergencyFundMonths:F1} months of essential expenses

FINANCIAL CAPACITY:
- Monthly Income: ${totalIncome:N2}
- Monthly Expenses: ${totalExpenses:N2}
- Essential Expenses: ${essentialExpenses:N2}
- Debt Payments: ${totalDebtPayments:N2}
- Available Cash Flow: ${availableCashFlow:N2}

INCOME BREAKDOWN:
{string.Join("\n", snapshot.Incomes.Select(i => $"- {i.Source}: ${i.MonthlyAmount:N2} ({(i.IsRecurring ? "Recurring" : "Variable")})"))}

Create a personalized savings strategy considering debt obligations and emergency fund status.
";
    }
}
