using Microsoft.AnalysisServices.Tabular;

var database = JsonSerializer.DeserializeDatabase(File.ReadAllText(args[0]), null, Microsoft.AnalysisServices.CompatibilityMode.PowerBI);
if (database.Model.Tables.Count < 10) throw new Exception("Incomplete semantic model");
var revenue = database.Model.Tables["Revenue"];
if (revenue.Columns.Find("mrr") is null) throw new Exception("Missing MRR column");
if (database.Model.Roles.Find("Regional Analyst") is null) throw new Exception("Missing RLS role");
if (database.Model.Tables["Period comparison"].CalculationGroup.CalculationItems.Count != 3)
    throw new Exception("Missing calculation items");
Console.WriteLine($"TOM deserialization passed: {database.Model.Tables.Count} tables, {database.Model.Relationships.Count} relationships.");
Console.WriteLine("This validates metadata, not DAX execution or Desktop rendering.");
