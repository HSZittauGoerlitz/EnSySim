% get public holidays for Saxony in the years 1991 to 2100
% create table for dates as datetime obj and description
% 13 public holdays per year in saxony
% Whit and easter sunday are ignored, since they are handled
% already correctly
nFreeDays = 11;
holydaysSN = table('Size', [110*nFreeDays, 2], ...
                   'VariableNames', ["date", "description"], ...
                   'VariableTypes', ["datetime", "string"]);
idxStart = 1;
idxStop = nFreeDays;
for year = 1991:2100
    htmlData = htmlTree(webread(sprintf('https://www.schulferien.org/deutschland/feiertage/%i/', year)));
    tableData = htmlData.findElement('table');
    publicHolidays = tableData.findElement('tr');
    publicHolidays = publicHolidays(publicHolidays.getAttribute('class') == "row_panel gesetzlich_row");
    % select only sn holidays
    publicHolidays = publicHolidays(contains(publicHolidays.string, "alle BL", 'IgnoreCase', false) | contains(publicHolidays.string, "SN", 'IgnoreCase', false));
    % get description text
    description = split(publicHolidays.string, '<DIV class="feiertag_responsive_small');
    description = description(:,1);
    description = regexprep(description, " +", " ");
    description = regexprep(description, '(?<=)(\<SPAN)(.*)(?=\<\/A)', '');
    description = description.split('</');
    description = description(:, 1);
    description = description.split('/">');
    description = description(:,2);
    description = description.strip();
    % get date
    date = regexprep(publicHolidays.string, '(.*)(?<=(Mo )|(Di )|(Mi )|(Do )|(Fr )|(Sa )|(So ))', '');
    date = regexprep(date, '(?=<)(.*)', '');
    date = datetime(date.strip());
    % add data
    holydaysSN.date(idxStart:idxStop) = date;
    holydaysSN.description(idxStart:idxStop) = description;
    % update idx
    idxStart = idxStop + 1;
    idxStop = idxStop + nFreeDays;
end