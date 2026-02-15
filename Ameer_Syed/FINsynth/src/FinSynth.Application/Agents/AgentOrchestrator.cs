using FinSynth.Domain.Entities;
using FinSynth.Domain.Interfaces;

namespace FinSynth.Application.Agents;

public class AgentOrchestrator : IAgentOrchestrator
{
    private readonly Dictionary<string, IFinancialAgent> _agents;
    private readonly IFinancialProfileRepository _profileRepo;
    
    public AgentOrchestrator(
        IEnumerable<IFinancialAgent> agents,
        IFinancialProfileRepository profileRepo)
    {
        _agents = agents.ToDictionary(a => a.AgentType, a => a);
        _profileRepo = profileRepo;
    }
    
    public async Task<Dictionary<string, string>> ProcessQueryAsync(
        string userId, 
        string query, 
        List<string>? specificAgents = null)
    {
        var profile = await _profileRepo.GetByUserIdAsync(userId);
        if (profile == null)
            throw new InvalidOperationException("User profile not found");
        
        var agentsToUse = specificAgents?.Select(a => _agents[a]).ToList() 
                         ?? DetermineRelevantAgents(query);
        
        var tasks = agentsToUse.Select(async agent => 
            new KeyValuePair<string, string>(
                agent.AgentType,
                await agent.AnalyzeAsync(profile, query)
            ));
        
        var results = await Task.WhenAll(tasks);
        return results.ToDictionary(r => r.Key, r => r.Value);
    }
    
    private List<IFinancialAgent> DetermineRelevantAgents(string query)
    {
        var queryLower = query.ToLowerInvariant();
        var relevantAgents = new List<IFinancialAgent>();
        
        if (queryLower.Contains("debt") || queryLower.Contains("payoff") || queryLower.Contains("credit"))
            relevantAgents.Add(_agents["DebtAnalyzer"]);
            
        if (queryLower.Contains("save") || queryLower.Contains("goal") || queryLower.Contains("emergency"))
            relevantAgents.Add(_agents["SavingsStrategy"]);
            
        if (queryLower.Contains("budget") || queryLower.Contains("spend") || queryLower.Contains("expense"))
            relevantAgents.Add(_agents["BudgetAdvisor"]);
        
        // If query is broad, use all agents
        if (relevantAgents.Count == 0)
            return _agents.Values.ToList();
            
        return relevantAgents;
    }
}
