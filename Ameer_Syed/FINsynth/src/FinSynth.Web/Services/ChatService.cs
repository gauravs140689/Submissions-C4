using FinSynth.Core.Abstractions;
using FinSynth.Core.Orchestration;
using System.Text.Json;

namespace FinSynth.Web.Services;

public class ChatService
{
    private readonly AgentCoordinator _coordinator;
    private readonly FinancialDataService _financialData;
    private readonly List<ChatMessage> _messages = new();

    public IReadOnlyList<ChatMessage> Messages => _messages;
    public event Action? OnMessagesChanged;

    public ChatService(AgentCoordinator coordinator, FinancialDataService financialData)
    {
        _coordinator = coordinator;
        _financialData = financialData;
    }

    public async Task<string> SendMessageAsync(string userMessage)
    {
        // Add user message
        _messages.Add(new ChatMessage
        {
            Role = "user",
            Content = userMessage,
            Timestamp = DateTime.Now
        });
        OnMessagesChanged?.Invoke();

        // Prepare request
        var context = new Dictionary<string, object>();
        
        if (_financialData.CurrentSnapshot != null)
        {
            context["financial_snapshot"] = JsonSerializer.Serialize(_financialData.CurrentSnapshot);
        }

        var request = new AgentRequest(userMessage, context);

        // Get agent response
        var response = await _coordinator.RouteAndExecuteAsync(request);

        // Add agent response
        var agentMessage = new ChatMessage
        {
            Role = "assistant",
            Content = response.Content,
            Timestamp = DateTime.Now,
            AgentId = response.AgentId,
            Confidence = response.Confidence,
            Metadata = response.Metadata
        };

        _messages.Add(agentMessage);
        OnMessagesChanged?.Invoke();

        return response.Content;
    }

    public void ClearHistory()
    {
        _messages.Clear();
        OnMessagesChanged?.Invoke();
    }
}

public class ChatMessage
{
    public string Role { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
    public string? AgentId { get; set; }
    public decimal? Confidence { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
}
