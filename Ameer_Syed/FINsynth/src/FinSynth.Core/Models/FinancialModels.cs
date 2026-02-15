namespace FinSynth.Core.Models;

public record DebtAccount(
    string AccountName,
    decimal Balance,
    decimal InterestRate,
    decimal MinimumPayment,
    string AccountType
);

public record Income(
    string Source,
    decimal MonthlyAmount,
    bool IsRecurring
);

public record Expense(
    string Category,
    decimal MonthlyAmount,
    bool IsEssential
);

public record FinancialSnapshot(
    List<Income> Incomes,
    List<Expense> Expenses,
    List<DebtAccount> Debts,
    decimal SavingsBalance,
    decimal EmergencyFundGoal
);

public record DebtPayoffPlan(
    string Strategy,
    List<DebtPayoffStep> Steps,
    decimal TotalInterestSaved,
    int MonthsToPayoff
);

public record DebtPayoffStep(
    int Month,
    string AccountName,
    decimal PaymentAmount,
    decimal RemainingBalance
);
