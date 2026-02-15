using FinSynth.Agents;
using FinSynth.Core.Abstractions;
using FinSynth.Core.Models;
using FinSynth.Core.Orchestration;
using Microsoft.Extensions.Configuration;
using System.Text.Json;

var config = new ConfigurationBuilder()
    .AddJsonFile("appsettings.json", optional: true)
    .AddEnvironmentVariables()
    .Build();

var apiKey = config["GOOGLE_API_KEY"] ?? 
    Environment.GetEnvironmentVariable("GOOGLE_API_KEY") ??
    throw new InvalidOperationException("GOOGLE_API_KEY not found");

Console.WriteLine("=== FinSynth Multi-Agent Test Harness (Google Gemini) ===\n");

// Sample financial data
var snapshot = new FinancialSnapshot(
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

Console.WriteLine("Financial Snapshot Loaded:");
Console.WriteLine($"Total Monthly Income: ${snapshot.Incomes.Sum(i => i.MonthlyAmount):N2}");
Console.WriteLine($"Total Monthly Expenses: ${snapshot.Expenses.Sum(e => e.MonthlyAmount):N2}");
Console.WriteLine($"Total Debt: ${snapshot.Debts.Sum(d => d.Balance):N2}");
Console.WriteLine($"Current Savings: ${snapshot.SavingsBalance:N2}\n");

// Initialize agents
var debtAgent = new DebtAnalyzerAgent(apiKey);
var savingsAgent = new SavingsStrategyAgent(apiKey);

// Create coordinator
var coordinator = new AgentCoordinator(new IFinancialAgent[] { debtAgent, savingsAgent });

Console.WriteLine($"Agents initialized: {coordinator.Agents.Count}");
foreach (var agent in coordinator.Agents.Values)
{
    Console.WriteLine($"  - {agent.Name} ({agent.AgentId})");
}
Console.WriteLine();

// Test queries
var queries = new[]
{
    "What's the fastest way to eliminate my debt while still saving some money?",
    "How should I build my emergency fund?",
    "Should I focus on debt or savings first?"
};

foreach (var query in queries)
{
    Console.WriteLine($"\n{'='}{new string('=', 100)}");
    Console.WriteLine($"QUERY: {query}");
    Console.WriteLine($"{'='}{new string('=', 100)}\n");

    var request = new AgentRequest(
        UserQuery: query,
        Context: new Dictionary<string, object>
        {
            ["financial_snapshot"] = JsonSerializer.Serialize(snapshot)
        }
    );

    Console.WriteLine("Routing query to appropriate agents...\n");

    var response = await coordinator.RouteAndExecuteAsync(request);

    if (response.Success)
    {
        Console.WriteLine($"Response from: {response.AgentId}");
        if (response.Metadata.ContainsKey("agents_consulted"))
        {
            Console.WriteLine($"Agents consulted: {response.Metadata["agents_consulted"]}");
        }
        Console.WriteLine($"Confidence: {response.Confidence:P0}");
        Console.WriteLine($"\n{response.Content}\n");
    }
    else
    {
        Console.WriteLine($"Error: {response.ErrorMessage}");
    }

    // Wait a bit between queries to avoid rate limiting
    if (query != queries.Last())
    {
        Console.WriteLine("\nWaiting 2 seconds before next query...");
        await Task.Delay(2000);
    }
}

Console.WriteLine($"\n\n{'='}{new string('=', 100)}");
Console.WriteLine("=== All Tests Complete ===");
Console.WriteLine($"{'='}{new string('=', 100)}");
