using FinSynth.Domain.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace FinSynth.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AgentController : ControllerBase
{
    private readonly IAgentOrchestrator _orchestrator;
    
    public AgentController(IAgentOrchestrator orchestrator)
    {
        _orchestrator = orchestrator;
    }
    
    [HttpPost("query")]
    public async Task<IActionResult> ProcessQuery([FromBody] AgentQueryRequest request)
    {
        var results = await _orchestrator.ProcessQueryAsync(
            request.UserId, 
            request.Query, 
            request.SpecificAgents);
        
        return Ok(new { Results = results });
    }
}

public record AgentQueryRequest(
    string UserId, 
    string Query, 
    List<string>? SpecificAgents = null);
