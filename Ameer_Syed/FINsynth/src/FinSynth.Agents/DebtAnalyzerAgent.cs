using FinSynth.Core;
using FinSynth.Core.Abstractions;
using FinSynth.Core.Models;
using System.Text.Json;

namespace FinSynth.Agents;

public class DebtAnalyzerAgent : GoogleGeminiAgentBase
{
    public override string AgentId => "debt-analyzer";
    public override string Name => "Debt Reduction Specialist";
    public override string Specialty => "Analyzes debt accounts and creates optimized payoff strategies";

    protected override string SystemPrompt => @"
You are a Debt Reduction Specialist with expertise in personal finance and debt management strategies.

Your responsibilities:
1. Analyze debt accounts (credit cards, loans, etc.) by balance, interest rate, and minimum payment
2. Recommend optimal payoff strategies (Avalanche, Snowball, or hybrid approaches)
3. Calculate total interest savings and payoff timelines
4. Provide actionable monthly payment plans

Analysis Framework:
- Avalanche Method: Pay highest interest rate first (maximizes savings)
- Snowball Method: Pay smallest balance first (psychological wins)
- Consider user's available cash flow and risk tolerance

Output Format:
- Clear strategy recommendation with justification
- Month-by-month payment allocation
- Total interest saved vs. minimum payments
- Payoff timeline
- Key milestones and warnings

Be direct, data-driven, and actionable. Avoid generic advice.
";

    public DebtAnalyzerAgent(string apiKey) : base(apiKey, "gemini-1.5-pro") { }

    protected override string BuildUserMessage(AgentRequest request)
    {
        if (!request.Context.TryGetValue("financial_snapshot", out var snapshotObj))
        {
            return base.BuildUserMessage(request);
        }

        var snapshot = JsonSerializer.Deserialize<FinancialSnapshot>(snapshotObj.ToString()!);
        if (snapshot == null) return base.BuildUserMessage(request);

        var debtSummary = string.Join("\n", snapshot.Debts.Select(d =>
            $"- {d.AccountName}: ${d.Balance:N2} @ {d.InterestRate}% APR (Min: ${d.MinimumPayment:N2})"
        ));

        var totalIncome = snapshot.Incomes.Sum(i => i.MonthlyAmount);
        var totalExpenses = snapshot.Expenses.Sum(e => e.MonthlyAmount);
        var totalDebtPayments = snapshot.Debts.Sum(d => d.MinimumPayment);
        var availableCashFlow = totalIncome - totalExpenses;

        return $@"
User Question: {request.UserQuery}

DEBT ACCOUNTS:
{debtSummary}

FINANCIAL CAPACITY:
- Monthly Income: ${totalIncome:N2}
- Monthly Expenses: ${totalExpenses:N2}
- Current Debt Payments: ${totalDebtPayments:N2}
- Available Cash Flow: ${availableCashFlow:N2}

Analyze this debt situation and provide a concrete payoff strategy.
";
    }
}
