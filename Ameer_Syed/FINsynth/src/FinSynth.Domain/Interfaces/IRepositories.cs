using FinSynth.Domain.Entities;

namespace FinSynth.Domain.Interfaces;

public interface IFinancialProfileRepository
{
    Task<FinancialProfile?> GetByUserIdAsync(string userId);
    Task<FinancialProfile> CreateAsync(FinancialProfile profile);
    Task<FinancialProfile> UpdateAsync(FinancialProfile profile);
}

public interface IAgentConversationRepository
{
    Task<AgentConversation?> GetByIdAsync(Guid id);
    Task<List<AgentConversation>> GetByUserIdAsync(string userId);
    Task<AgentConversation> CreateAsync(AgentConversation conversation);
    Task AddMessageAsync(Guid conversationId, AgentMessage message);
}

public interface IAgentRecommendationRepository
{
    Task<List<AgentRecommendation>> GetByConversationIdAsync(Guid conversationId);
    Task<AgentRecommendation> CreateAsync(AgentRecommendation recommendation);
}
