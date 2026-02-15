namespace FinSynth.Domain.Entities;

public class AgentConversation
{
    public Guid Id { get; set; }
    public string UserId { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public List<AgentMessage> Messages { get; set; } = new();
}

public class AgentMessage
{
    public Guid Id { get; set; }
    public Guid ConversationId { get; set; }
    public string AgentType { get; set; } = string.Empty; // DebtAnalyzer, SavingsStrategy, BudgetAdvisor
    public string Role { get; set; } = string.Empty; // user, assistant
    public string Content { get; set; } = string.Empty;
    public string? MetadataJson { get; set; }
    public DateTime Timestamp { get; set; }
}

public class AgentRecommendation
{
    public Guid Id { get; set; }
    public Guid ConversationId { get; set; }
    public string AgentType { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string ActionItemsJson { get; set; } = string.Empty;
    public decimal? ProjectedImpact { get; set; }
    public DateTime CreatedAt { get; set; }
}
