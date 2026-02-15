namespace FinSynth.Core.Abstractions;

public interface IFinancialAgent
{
    string AgentId { get; }
    string Name { get; }
    string Specialty { get; }
    Task<AgentResponse> ProcessAsync(AgentRequest request, CancellationToken cancellationToken = default);
}

public record AgentRequest(
    string UserQuery,
    Dictionary<string, object> Context,
    string? ConversationId = null
);

public record AgentResponse(
    string AgentId,
    string Content,
    decimal Confidence,
    Dictionary<string, object> Metadata,
    bool Success = true,
    string? ErrorMessage = null
);
