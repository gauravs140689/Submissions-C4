using FinSynth.Core.Models;

namespace FinSynth.Web.Services;

public class FinancialDataService
{
    private FinancialSnapshot? _currentSnapshot;
    
    public event Action? OnSnapshotChanged;

    public FinancialSnapshot? CurrentSnapshot => _currentSnapshot;

    public void UpdateSnapshot(FinancialSnapshot snapshot)
    {
        _currentSnapshot = snapshot;
        OnSnapshotChanged?.Invoke();
    }

    public void AddIncome(Income income)
    {
        if (_currentSnapshot == null) return;
        
        var incomes = _currentSnapshot.Incomes.ToList();
        incomes.Add(income);
        
        _currentSnapshot = _currentSnapshot with { Incomes = incomes };
        OnSnapshotChanged?.Invoke();
    }

    public void AddExpense(Expense expense)
    {
        if (_currentSnapshot == null) return;
        
        var expenses = _currentSnapshot.Expenses.ToList();
        expenses.Add(expense);
        
        _currentSnapshot = _currentSnapshot with { Expenses = expenses };
        OnSnapshotChanged?.Invoke();
    }

    public void AddDebt(DebtAccount debt)
    {
        if (_currentSnapshot == null) return;
        
        var debts = _currentSnapshot.Debts.ToList();
        debts.Add(debt);
        
        _currentSnapshot = _currentSnapshot with { Debts = debts };
        OnSnapshotChanged?.Invoke();
    }

    public void RemoveIncome(int index)
    {
        if (_currentSnapshot == null || index < 0 || index >= _currentSnapshot.Incomes.Count) return;
        
        var incomes = _currentSnapshot.Incomes.ToList();
        incomes.RemoveAt(index);
        
        _currentSnapshot = _currentSnapshot with { Incomes = incomes };
        OnSnapshotChanged?.Invoke();
    }

    public void RemoveExpense(int index)
    {
        if (_currentSnapshot == null || index < 0 || index >= _currentSnapshot.Expenses.Count) return;
        
        var expenses = _currentSnapshot.Expenses.ToList();
        expenses.RemoveAt(index);
        
        _currentSnapshot = _currentSnapshot with { Expenses = expenses };
        OnSnapshotChanged?.Invoke();
    }

    public void RemoveDebt(int index)
    {
        if (_currentSnapshot == null || index < 0 || index >= _currentSnapshot.Debts.Count) return;
        
        var debts = _currentSnapshot.Debts.ToList();
        debts.RemoveAt(index);
        
        _currentSnapshot = _currentSnapshot with { Debts = debts };
        OnSnapshotChanged?.Invoke();
    }

    public void UpdateSavings(decimal savingsBalance, decimal emergencyFundGoal)
    {
        if (_currentSnapshot == null) return;
        
        _currentSnapshot = _currentSnapshot with 
        { 
            SavingsBalance = savingsBalance,
            EmergencyFundGoal = emergencyFundGoal
        };
        OnSnapshotChanged?.Invoke();
    }

    public void InitializeWithSampleData()
    {
        _currentSnapshot = new FinancialSnapshot(
            Incomes: new List<Income>
            {
                new("Salary", 5500m, true),
                new("Freelance", 800m, false)
            },
            Expenses: new List<Expense>
            {
                new("Rent", 1500m, true),
                new("Groceries", 600m, true),
                new("Transportation", 200m, true),
                new("Utilities", 150m, true),
                new("Entertainment", 300m, false)
            },
            Debts: new List<DebtAccount>
            {
                new("Chase Visa", 8500m, 18.99m, 170m, "Credit Card"),
                new("Discover Card", 3200m, 22.49m, 96m, "Credit Card"),
                new("Personal Loan", 12000m, 9.5m, 350m, "Installment"),
                new("Car Loan", 18500m, 5.25m, 425m, "Auto")
            },
            SavingsBalance: 2500m,
            EmergencyFundGoal: 12000m
        );
        OnSnapshotChanged?.Invoke();
    }
}
