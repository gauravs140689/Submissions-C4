using FinSynth.Core.Models;
using System.Text.Json;

namespace FinSynth.Web.Services;

public class FileProcessingService
{
    private readonly string _uploadPath;

    public FileProcessingService(IWebHostEnvironment env)
    {
        _uploadPath = Path.Combine(env.WebRootPath, "uploads");
        if (!Directory.Exists(_uploadPath))
        {
            Directory.CreateDirectory(_uploadPath);
        }
    }

    public async Task<string> SaveFileAsync(Stream fileStream, string fileName)
    {
        var uniqueFileName = $"{Guid.NewGuid()}_{fileName}";
        var filePath = Path.Combine(_uploadPath, uniqueFileName);

        using (var fs = new FileStream(filePath, FileMode.Create))
        {
            await fileStream.CopyToAsync(fs);
        }

        return uniqueFileName;
    }

    public async Task<FinancialSnapshot?> ParseFinancialDocumentAsync(string fileName)
    {
        var filePath = Path.Combine(_uploadPath, fileName);
        
        if (!File.Exists(filePath))
            return null;

        var extension = Path.GetExtension(fileName).ToLower();

        return extension switch
        {
            ".json" => await ParseJsonAsync(filePath),
            ".csv" => await ParseCsvAsync(filePath),
            // PDF and Excel parsing would require additional libraries
            _ => null
        };
    }

    private async Task<FinancialSnapshot?> ParseJsonAsync(string filePath)
    {
        try
        {
            var json = await File.ReadAllTextAsync(filePath);
            return JsonSerializer.Deserialize<FinancialSnapshot>(json);
        }
        catch
        {
            return null;
        }
    }

    private async Task<FinancialSnapshot?> ParseCsvAsync(string filePath)
    {
        // Simplified CSV parsing - in production, use a proper CSV library
        // This is a placeholder for demonstration
        await Task.CompletedTask;
        return new FinancialSnapshot(
            new List<Income>(),
            new List<Expense>(),
            new List<DebtAccount>(),
            0m,
            0m
        );
    }

    public async Task<List<string>> GetUploadedFilesAsync()
    {
        await Task.CompletedTask;
        return Directory.GetFiles(_uploadPath)
            .Select(Path.GetFileName)
            .Where(f => f != null)
            .Cast<string>()
            .ToList();
    }

    public void DeleteFile(string fileName)
    {
        var filePath = Path.Combine(_uploadPath, fileName);
        if (File.Exists(filePath))
        {
            File.Delete(filePath);
        }
    }
}
