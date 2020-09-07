% get public holidays for Saxony in the years 1990 to 2100
% create table for dates as datetime obj and description
% 13 public holdays per year in saxony
holydaysSN = table('Size', [110*13, 2], ...
                   'VariableNames', ["date", "description"], ...
                   'VariableTypes', ["datetime", "string"]);
for year = 1990:2100
    
end