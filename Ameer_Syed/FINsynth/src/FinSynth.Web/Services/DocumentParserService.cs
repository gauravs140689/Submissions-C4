using FinSynth.Core.Models;
using OfficeOpenXml;
using System.Text.RegularExpressions;

namespace FinSynth.Web.Services;

public class DocumentParserService
{
    public async Task<FinancialSnapshot> ParseDocumentAsync(Stream fileStream, string fileName)
    {
        var extension = System.IO.Path.GetExtension(fileName).ToLowerInvariant();

        return extension switch
        {
            ".pdf" => await ParsePdfAsync(fileStream),
            ".xlsx" or ".xls" => await ParseExcelAsync(fileStream),
            ".csv" => await ParseCsvAsync(fileStream),
            _ => throw new NotSupportedException($"File type {extension} not supported")
        };
    }

    private async Task<FinancialSnapshot> ParsePdfAsync(Stream stream)
    {
        // PDF parsing is complex - for now return empty snapshot
        // User will see message to enter data manually
        return CreateEmptySnapshot();
    }

    private async Task<FinancialSnapshot> ParseExcelAsync(Stream stream)
    {
        ExcelPackage.LicenseContext = LicenseContext.NonCommercial;
        
        using var package = new ExcelPackage(stream);
        var worksheet = package.Workbook.Worksheets.FirstOrDefault();
        
        if (worksheet == null)
            return CreateEmptySnapshot();

        var incomes = new List<Income>();
        var expenses = new List<Expense>();
        var debts = new List<DebtAccount>();

        // Simple parsing - assumes columns: Type, Description, Amount, Category/Rate
        for (int row = 2; row <= worksheet.Dimension.End.Row; row++)
        {
            var type = worksheet.Cells[row, 1].Text.Trim();
            var description = worksheet.Cells[row, 2].Text.Trim();
            var amountText = worksheet.Cells[row, 3].Text.Trim();
            var extra = worksheet.Cells[row, 4].Text.Trim();

            if (string.IsNullOrWhiteSpace(description) || string.IsNullOrWhiteSpace(amountText))
                continue;

            if (!decimal.TryParse(amountText.Replace("$", "").Replace(",", ""), out var amount))
                continue;

            switch (type.ToLower())
            {
                case "income":
                    incomes.Add(new Income(description, amount, true));
                    break;
                case "expense":
                    var isEssential = extra.ToLower().Contains("essential") || extra.ToLower().Contains("need");
                    expenses.Add(new Expense(description, amount, isEssential));
                    break;
                case "debt":
                    if (decimal.TryParse(extra.Replace("%", ""), out var rate))
                    {
                        var minPayment = amount * 0.02m; // Assume 2% minimum
                        debts.Add(new DebtAccount(description, amount, rate, minPayment, "Debt"));
                    }
                    break;
            }
        }

        return new FinancialSnapshot(incomes, expenses, debts, 0m, 0m);
    }

    private async Task<FinancialSnapshot> ParseCsvAsync(Stream stream)
    {
        using var reader = new StreamReader(stream);
        var content = await reader.ReadToEndAsync();
        var lines = content.Split('\n').Skip(1); // Skip header

        var incomes = new List<Income>();
        var expenses = new List<Expense>();
        var debts = new List<DebtAccount>();

        foreach (var line in lines)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            
            var parts = line.Split(',');
            if (parts.Length < 3) continue;

            var type = parts[0].Trim().Trim('"');
            var description = parts[1].Trim().Trim('"');
            var amountText = parts[2].Trim().Trim('"');

            if (!decimal.TryParse(amountText.Replace("$", "").Replace(",", ""), out var amount))
                continue;

            switch (type.ToLower())
            {
                case "income":
                    incomes.Add(new Income(description, amount, true));
                    break;
                case "expense":
                    expenses.Add(new Expense(description, amount, true));
                    break;
                case "debt":
                    var rate = parts.Length > 3 && decimal.TryParse(parts[3].Replace("%", ""), out var r) ? r : 10m;
                    var minPayment = amount * 0.02m;
                    debts.Add(new DebtAccount(description, amount, rate, minPayment, "Debt"));
                    break;
            }
        }

        return new FinancialSnapshot(incomes, expenses, debts, 0m, 0m);
    }

    private FinancialSnapshot CreateEmptySnapshot()
    {
        return new FinancialSnapshot(
            new List<Income>(),
            new List<Expense>(),
            new List<DebtAccount>(),
            0m,
            0m
        );
    }
}
