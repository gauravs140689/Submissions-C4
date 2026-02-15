using Anthropic.SDK;
using Anthropic.SDK.Messaging;
using FinSynth.Domain.Entities;
using FinSynth.Domain.Interfaces;
using System.Text.Json;

namespace FinSynth.Application.Agents;

public abstract class BaseAgent : IFinancialAgent
{
    protected readonly AnthropicClient _anthropic;
    
    public abstract string AgentType { get; }
    protected abstract string SystemPrompt { get; }
    
    protected BaseAgent(string apiKey)
    {
        _anthropic = new AnthropicClient(new APIAuthentication(apiKey));
    }
    
    public async Task<string> AnalyzeAsync(FinancialProfile profile, string userQuery)
    {
        var profileContext = BuildProfileContext(profile);
        var messages = new List<Message>
        {
            new Message(RoleType.User, $"{profileContext}\n\nUser Question: {userQuery}")
        };
        
        var parameters = new MessageParameters
        {
            Messages = messages,
            Model = AnthropicModels.Claude35Sonnet,
            Stream = false,
            Temperature = 0.7m,
            MaxTokens = 2048,
            System = new List<SystemMessage> { new SystemMessage(SystemPrompt) }
        };
        
        var response = await _anthropic.Messages.GetClaudeMessageAsync(parameters);
        return response.Content.First()?.Text ?? "No response generated.";
    }
    
    protected virtual string BuildProfileContext(FinancialProfile profile)
    {
        return $@"FINANCIAL PROFILE:
Monthly Income: ${profile.MonthlyIncome:N2}

DEBTS ({profile.Debts.Count}):
{string.Join("\n", profile.Debts.Select(d => 
    $"- {d.Name}: ${d.Balance:N2} @ {d.InterestRate}% APR, Min Payment: ${d.MinimumPayment:N2}"))}

EXPENSES ({profile.Expenses.Count}):
{string.Join("\n", profile.Expenses.Select(e => 
    $"- {e.Category}: ${e.Amount:N2} ({e.Frequency}){(e.IsEssential ? " [Essential]" : "")}"))}

SAVINGS GOALS ({profile.SavingsGoals.Count}):
{string.Join("\n", profile.SavingsGoals.Select(g => 
    $"- {g.Name}: ${g.CurrentAmount:N2}/${g.TargetAmount:N2} by {g.TargetDate:yyyy-MM-dd} (Priority {g.Priority})"))}";
    }
}
