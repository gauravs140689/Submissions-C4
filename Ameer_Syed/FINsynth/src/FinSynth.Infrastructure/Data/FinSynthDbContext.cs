using FinSynth.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FinSynth.Infrastructure.Data;

public class FinSynthDbContext : DbContext
{
    public FinSynthDbContext(DbContextOptions<FinSynthDbContext> options) : base(options) { }
    
    public DbSet<FinancialProfile> FinancialProfiles { get; set; }
    public DbSet<Debt> Debts { get; set; }
    public DbSet<Expense> Expenses { get; set; }
    public DbSet<SavingsGoal> SavingsGoals { get; set; }
    public DbSet<AgentConversation> AgentConversations { get; set; }
    public DbSet<AgentMessage> AgentMessages { get; set; }
    public DbSet<AgentRecommendation> AgentRecommendations { get; set; }
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<FinancialProfile>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.UserId).IsUnique();
            entity.Property(e => e.MonthlyIncome).HasPrecision(18, 2);
        });
        
        modelBuilder.Entity<Debt>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Balance).HasPrecision(18, 2);
            entity.Property(e => e.InterestRate).HasPrecision(5, 2);
            entity.Property(e => e.MinimumPayment).HasPrecision(18, 2);
        });
        
        modelBuilder.Entity<Expense>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Amount).HasPrecision(18, 2);
        });
        
        modelBuilder.Entity<SavingsGoal>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.TargetAmount).HasPrecision(18, 2);
            entity.Property(e => e.CurrentAmount).HasPrecision(18, 2);
        });
        
        modelBuilder.Entity<AgentConversation>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.UserId);
        });
        
        modelBuilder.Entity<AgentMessage>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.ConversationId);
        });
        
        modelBuilder.Entity<AgentRecommendation>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.ConversationId);
            entity.Property(e => e.ProjectedImpact).HasPrecision(18, 2);
        });
    }
}
