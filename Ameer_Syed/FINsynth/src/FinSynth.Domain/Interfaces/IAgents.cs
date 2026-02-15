using FinSynth.Domain.Entities;

namespace FinSynth.Domain.Interfaces;

public interface IFinancialAgent
{
    string AgentType { get; }
    Task<string> AnalyzeAsync(FinancialProfile profile, string userQuery);
}

public interface IAgentOrchestrator
{
    Task<Dictionary<string, string>> ProcessQueryAsync(
        string userId, 
        string query, 
        List<string>? specificAgents = null);
}
