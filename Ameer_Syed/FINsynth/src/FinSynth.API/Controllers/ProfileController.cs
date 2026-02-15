using FinSynth.Domain.Entities;
using FinSynth.Domain.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace FinSynth.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProfileController : ControllerBase
{
    private readonly IFinancialProfileRepository _repository;
    
    public ProfileController(IFinancialProfileRepository repository)
    {
        _repository = repository;
    }
    
    [HttpGet("{userId}")]
    public async Task<IActionResult> GetProfile(string userId)
    {
        var profile = await _repository.GetByUserIdAsync(userId);
        return profile != null ? Ok(profile) : NotFound();
    }
    
    [HttpPost]
    public async Task<IActionResult> CreateProfile([FromBody] FinancialProfile profile)
    {
        profile.Id = Guid.NewGuid();
        profile.CreatedAt = DateTime.UtcNow;
        profile.UpdatedAt = DateTime.UtcNow;
        
        var created = await _repository.CreateAsync(profile);
        return CreatedAtAction(nameof(GetProfile), new { userId = created.UserId }, created);
    }
    
    [HttpPut]
    public async Task<IActionResult> UpdateProfile([FromBody] FinancialProfile profile)
    {
        var updated = await _repository.UpdateAsync(profile);
        return Ok(updated);
    }
}
