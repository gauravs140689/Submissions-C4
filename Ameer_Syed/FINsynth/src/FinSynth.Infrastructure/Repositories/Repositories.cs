using FinSynth.Domain.Entities;
using FinSynth.Domain.Interfaces;
using FinSynth.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace FinSynth.Infrastructure.Repositories;

public class FinancialProfileRepository : IFinancialProfileRepository
{
    private readonly FinSynthDbContext _context;
    
    public FinancialProfileRepository(FinSynthDbContext context)
    {
        _context = context;
    }
    
    public async Task<FinancialProfile?> GetByUserIdAsync(string userId)
    {
        return await _context.FinancialProfiles
            .Include(p => p.Debts)
            .Include(p => p.Expenses)
            .Include(p => p.SavingsGoals)
            .FirstOrDefaultAsync(p => p.UserId == userId);
    }
    
    public async Task<FinancialProfile> CreateAsync(FinancialProfile profile)
    {
        _context.FinancialProfiles.Add(profile);
        await _context.SaveChangesAsync();
        return profile;
    }
    
    public async Task<FinancialProfile> UpdateAsync(FinancialProfile profile)
    {
        profile.UpdatedAt = DateTime.UtcNow;
        _context.FinancialProfiles.Update(profile);
        await _context.SaveChangesAsync();
        return profile;
    }
}

public class AgentConversationRepository : IAgentConversationRepository
{
    private readonly FinSynthDbContext _context;
    
    public AgentConversationRepository(FinSynthDbContext context)
    {
        _context = context;
    }
    
    public async Task<AgentConversation?> GetByIdAsync(Guid id)
    {
        return await _context.AgentConversations
            .Include(c => c.Messages)
            .FirstOrDefaultAsync(c => c.Id == id);
    }
    
    public async Task<List<AgentConversation>> GetByUserIdAsync(string userId)
    {
        return await _context.AgentConversations
            .Include(c => c.Messages)
            .Where(c => c.UserId == userId)
            .OrderByDescending(c => c.CreatedAt)
            .ToListAsync();
    }
    
    public async Task<AgentConversation> CreateAsync(AgentConversation conversation)
    {
        _context.AgentConversations.Add(conversation);
        await _context.SaveChangesAsync();
        return conversation;
    }
    
    public async Task AddMessageAsync(Guid conversationId, AgentMessage message)
    {
        message.ConversationId = conversationId;
        _context.AgentMessages.Add(message);
        await _context.SaveChangesAsync();
    }
}

public class AgentRecommendationRepository : IAgentRecommendationRepository
{
    private readonly FinSynthDbContext _context;
    
    public AgentRecommendationRepository(FinSynthDbContext context)
    {
        _context = context;
    }
    
    public async Task<List<AgentRecommendation>> GetByConversationIdAsync(Guid conversationId)
    {
        return await _context.AgentRecommendations
            .Where(r => r.ConversationId == conversationId)
            .OrderByDescending(r => r.CreatedAt)
            .ToListAsync();
    }
    
    public async Task<AgentRecommendation> CreateAsync(AgentRecommendation recommendation)
    {
        _context.AgentRecommendations.Add(recommendation);
        await _context.SaveChangesAsync();
        return recommendation;
    }
}
