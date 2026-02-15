using Mscc.GenerativeAI;
using FinSynth.Core.Abstractions;

namespace FinSynth.Core;

public abstract class GoogleGeminiAgentBase : IFinancialAgent
{
    private readonly GoogleAI _client;
    private readonly GenerativeModel _model;
    protected abstract string SystemPrompt { get; }

    public abstract string AgentId { get; }
    public abstract string Name { get; }
    public abstract string Specialty { get; }

    protected GoogleGeminiAgentBase(string apiKey, string modelName = "gemini-1.5-pro")
    {
        _client = new GoogleAI(apiKey);
        _model = _client.GenerativeModel(model: modelName);
    }

    public virtual async Task<AgentResponse> ProcessAsync(AgentRequest request, CancellationToken cancellationToken = default)
    {
        try
        {
            var fullPrompt = $@"{SystemPrompt}

---

{BuildUserMessage(request)}";

            var response = await _model.GenerateContent(fullPrompt);

            var content = response?.Text ?? string.Empty;

            return new AgentResponse(
                AgentId,
                content,
                CalculateConfidence(content),
                ExtractMetadata(response),
                Success: true
            );
        }
        catch (Exception ex)
        {
            return new AgentResponse(
                AgentId,
                string.Empty,
                0m,
                new Dictionary<string, object>(),
                Success: false,
                ErrorMessage: ex.Message
            );
        }
    }

    protected virtual string BuildUserMessage(AgentRequest request)
    {
        var contextInfo = string.Join("\n", request.Context.Select(kvp => $"{kvp.Key}: {kvp.Value}"));
        return $"{request.UserQuery}\n\nContext:\n{contextInfo}";
    }

    protected virtual decimal CalculateConfidence(string content)
    {
        // Simple heuristic: longer, structured responses = higher confidence
        return content.Length > 500 ? 0.85m : 0.70m;
    }

    protected virtual Dictionary<string, object> ExtractMetadata(GenerateContentResponse? response)
    {
        var metadata = new Dictionary<string, object>
        {
            ["model"] = "gemini",
            ["provider"] = "google"
        };

        if (response?.UsageMetadata != null)
        {
            metadata["usage_prompt_tokens"] = response.UsageMetadata.PromptTokenCount;
            metadata["usage_completion_tokens"] = response.UsageMetadata.CandidatesTokenCount;
            metadata["usage_total_tokens"] = response.UsageMetadata.TotalTokenCount;
        }

        return metadata;
    }
}
