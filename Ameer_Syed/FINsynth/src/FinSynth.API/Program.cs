using FinSynth.Application.Agents;
using FinSynth.Domain.Interfaces;
using FinSynth.Infrastructure.Data;
using FinSynth.Infrastructure.Repositories;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Database
builder.Services.AddDbContext<FinSynthDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// Repositories
builder.Services.AddScoped<IFinancialProfileRepository, FinancialProfileRepository>();
builder.Services.AddScoped<IAgentConversationRepository, AgentConversationRepository>();
builder.Services.AddScoped<IAgentRecommendationRepository, AgentRecommendationRepository>();

// Agents
var anthropicApiKey = builder.Configuration["Anthropic:ApiKey"] ?? throw new InvalidOperationException("Anthropic API key not configured");
builder.Services.AddSingleton<IFinancialAgent>(new DebtAnalyzerAgent(anthropicApiKey));
builder.Services.AddSingleton<IFinancialAgent>(new SavingsStrategyAgent(anthropicApiKey));
builder.Services.AddSingleton<IFinancialAgent>(new BudgetAdvisorAgent(anthropicApiKey));
builder.Services.AddScoped<IAgentOrchestrator, AgentOrchestrator>();

// CORS for Blazor
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowBlazor", policy =>
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseCors("AllowBlazor");
app.UseAuthorization();
app.MapControllers();

app.Run();
