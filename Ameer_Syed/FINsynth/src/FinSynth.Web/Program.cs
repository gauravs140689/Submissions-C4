using FinSynth.Agents;
using FinSynth.Core.Abstractions;
using FinSynth.Core.Orchestration;
using FinSynth.Web.Services;
using Radzen;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorPages();
builder.Services.AddServerSideBlazor();

// Radzen services for charts and UI
builder.Services.AddRadzenComponents();

// API Key configuration
var googleApiKey = builder.Configuration["GOOGLE_API_KEY"] ?? 
    Environment.GetEnvironmentVariable("GOOGLE_API_KEY") ??
    throw new InvalidOperationException("GOOGLE_API_KEY not configured");

// Register agents
builder.Services.AddSingleton<IFinancialAgent>(sp => new DebtAnalyzerAgent(googleApiKey));
builder.Services.AddSingleton<IFinancialAgent>(sp => new SavingsStrategyAgent(googleApiKey));
builder.Services.AddSingleton<IFinancialAgent>(sp => new BudgetAdvisorAgent(googleApiKey));

// Register agent coordinator
builder.Services.AddSingleton<AgentCoordinator>(sp =>
{
    var agents = sp.GetServices<IFinancialAgent>();
    return new AgentCoordinator(agents);
});

// Register application services
builder.Services.AddScoped<DocumentParserService>();
builder.Services.AddScoped<FinancialDataService>();
builder.Services.AddScoped<ChatService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();

app.MapBlazorHub();
app.MapFallbackToPage("/_Host");

app.Run();
