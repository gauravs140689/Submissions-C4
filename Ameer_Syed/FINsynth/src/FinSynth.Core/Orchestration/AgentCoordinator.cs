using FinSynth.Core.Abstractions;

namespace FinSynth.Core.Orchestration;

public class AgentCoordinator
{
    private readonly Dictionary<string, IFinancialAgent> _agents;

    public AgentCoordinator(IEnumerable<IFinancialAgent> agents)
    {
        _agents = agents.ToDictionary(a => a.AgentId, a => a);
    }

    public IReadOnlyDictionary<string, IFinancialAgent> Agents => _agents;

    /// <summary>
    /// Execute a single agent by ID
    /// </summary>
    public async Task<AgentResponse> ExecuteAgentAsync(
        string agentId, 
        AgentRequest request, 
        CancellationToken cancellationToken = default)
    {
        if (!_agents.TryGetValue(agentId, out var agent))
        {
            return new AgentResponse(
                agentId,
                string.Empty,
                0m,
                new Dictionary<string, object>(),
                Success: false,
                ErrorMessage: $"Agent '{agentId}' not found"
            );
        }

        return await agent.ProcessAsync(request, cancellationToken);
    }

    /// <summary>
    /// Execute multiple agents in parallel
    /// </summary>
    public async Task<Dictionary<string, AgentResponse>> ExecuteMultipleAsync(
        string[] agentIds,
        AgentRequest request,
        CancellationToken cancellationToken = default)
    {
        var tasks = agentIds
            .Where(id => _agents.ContainsKey(id))
            .Select(async id => new
            {
                AgentId = id,
                Response = await _agents[id].ProcessAsync(request, cancellationToken)
            });

        var results = await Task.WhenAll(tasks);

        return results.ToDictionary(r => r.AgentId, r => r.Response);
    }

    /// <summary>
    /// Route query to most appropriate agent(s) based on keywords
    /// </summary>
    public async Task<AgentResponse> RouteAndExecuteAsync(
        AgentRequest request,
        CancellationToken cancellationToken = default)
    {
        var selectedAgents = DetermineRelevantAgents(request.UserQuery);

        if (selectedAgents.Length == 0)
        {
            return new AgentResponse(
                "coordinator",
                "I couldn't determine which specialist should handle your query. Could you be more specific?",
                0.5m,
                new Dictionary<string, object> { ["matched_agents"] = 0 },
                Success: true
            );
        }

        if (selectedAgents.Length == 1)
        {
            return await ExecuteAgentAsync(selectedAgents[0], request, cancellationToken);
        }

        // Multiple agents needed - execute in parallel and synthesize
        var responses = await ExecuteMultipleAsync(selectedAgents, request, cancellationToken);
        return await SynthesizeResponsesAsync(request, responses, cancellationToken);
    }

    /// <summary>
    /// Determine which agents are relevant based on query keywords
    /// </summary>
    private string[] DetermineRelevantAgents(string query)
    {
        var queryLower = query.ToLower();
        var relevantAgents = new List<string>();

        // Debt-related keywords
        if (queryLower.Contains("debt") || 
            queryLower.Contains("credit card") || 
            queryLower.Contains("loan") ||
            queryLower.Contains("payoff") ||
            queryLower.Contains("interest"))
        {
            relevantAgents.Add("debt-analyzer");
        }

        // Savings-related keywords
        if (queryLower.Contains("save") || 
            queryLower.Contains("saving") || 
            queryLower.Contains("emergency fund") ||
            queryLower.Contains("goal") ||
            queryLower.Contains("invest"))
        {
            relevantAgents.Add("savings-strategy");
        }

        // Budget-related keywords
        if (queryLower.Contains("budget") || 
            queryLower.Contains("expense") || 
            queryLower.Contains("spending") ||
            queryLower.Contains("cut costs") ||
            queryLower.Contains("reduce spending"))
        {
            relevantAgents.Add("budget-advisor");
        }

        return relevantAgents.ToArray();
    }

    /// <summary>
    /// Synthesize multiple agent responses into cohesive advice
    /// </summary>
    private async Task<AgentResponse> SynthesizeResponsesAsync(
        AgentRequest originalRequest,
        Dictionary<string, AgentResponse> agentResponses,
        CancellationToken cancellationToken = default)
    {
        var successfulResponses = agentResponses
            .Where(kvp => kvp.Value.Success)
            .ToList();

        if (successfulResponses.Count == 0)
        {
            return new AgentResponse(
                "coordinator",
                "All agents failed to process the request.",
                0m,
                new Dictionary<string, object>(),
                Success: false,
                ErrorMessage: "Multiple agent failures"
            );
        }

        // Build synthesized response
        var synthesis = "=== COMPREHENSIVE FINANCIAL ANALYSIS ===\n\n";

        foreach (var (agentId, response) in successfulResponses)
        {
            var agent = _agents[agentId];
            synthesis += $"## {agent.Name}\n\n{response.Content}\n\n";
            synthesis += new string('-', 80) + "\n\n";
        }

        synthesis += "=== SYNTHESIS ===\n\n";
        synthesis += "The above recommendations from our specialist agents should be considered together. ";
        synthesis += "Balance debt reduction with emergency fund building, and adjust your strategy as your situation improves.";

        var avgConfidence = successfulResponses.Average(r => r.Value.Confidence);

        return new AgentResponse(
            "coordinator",
            synthesis,
            avgConfidence,
            new Dictionary<string, object>
            {
                ["agents_consulted"] = successfulResponses.Count,
                ["agent_ids"] = string.Join(", ", successfulResponses.Select(r => r.Key))
            },
            Success: true
        );
    }
}
