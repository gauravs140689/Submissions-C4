namespace FinSynth.Domain.Entities;

public class FinancialProfile
{
    public Guid Id { get; set; }
    public string UserId { get; set; } = string.Empty;
    public decimal MonthlyIncome { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    
    public List<Debt> Debts { get; set; } = new();
    public List<Expense> Expenses { get; set; } = new();
    public List<SavingsGoal> SavingsGoals { get; set; } = new();
}

public class Debt
{
    public Guid Id { get; set; }
    public Guid ProfileId { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal Balance { get; set; }
    public decimal InterestRate { get; set; }
    public decimal MinimumPayment { get; set; }
    public string DebtType { get; set; } = string.Empty; // CreditCard, StudentLoan, Mortgage, etc.
}

public class Expense
{
    public Guid Id { get; set; }
    public Guid ProfileId { get; set; }
    public string Category { get; set; } = string.Empty;
    public decimal Amount { get; set; }
    public string Frequency { get; set; } = "Monthly"; // Monthly, Annual, OneTime
    public bool IsEssential { get; set; }
}

public class SavingsGoal
{
    public Guid Id { get; set; }
    public Guid ProfileId { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal TargetAmount { get; set; }
    public decimal CurrentAmount { get; set; }
    public DateTime TargetDate { get; set; }
    public int Priority { get; set; } // 1-5
}
