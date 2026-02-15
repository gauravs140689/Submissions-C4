using FinSynth.Core.Abstractions;
using FinSynth.Core.Orchestration;

namespace FinSynth.Web.Services;

public class AgentService
{
    private readonly AgentCoordinator _coordinator;

    public AgentService(AgentCoordinator coordinator)
    {
        _coordinator = coordinator;
    }

    public IReadOnlyDictionary<string, IFinancialAgent> GetAvailableAgents()
    {
        return _coordinator.Agents;
    }

    public async Task<AgentResponse> AskAgentAsync(string agentId, string query, Dictionary<string, object> context)
    {
        var request = new AgentRequest(query, context);
        return await _coordinator.ExecuteAgentAsync(agentId, request);
    }

    public async Task<AgentResponse> AskMultipleAgentsAsync(string query, Dictionary<string, object> context)
    {
        var request = new AgentRequest(query, context);
        return await _coordinator.RouteAndExecuteAsync(request);
    }

    public async Task<Dictionary<string, AgentResponse>> GetAllAgentResponsesAsync(string query, Dictionary<string, object> context)
    {
        var request = new AgentRequest(query, context);
        var agentIds = _coordinator.Agents.Keys.ToArray();
        return await _coordinator.ExecuteMultipleAsync(agentIds, request);
    }
}
