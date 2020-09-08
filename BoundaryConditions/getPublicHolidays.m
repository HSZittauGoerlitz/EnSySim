% get public holidays for Saxony in the years 1990 to 2100
% create table for dates as datetime obj and description
% 13 public holdays per year in saxony
nFreeDays = 13;
holydaysSN = table('Size', [110*nFreeDays, 2], ...
                   'VariableNames', ["date", "description"], ...
                   'VariableTypes', ["datetime", "string"]);
idxStart = 1;
idxStop = nFreeDays;
for year = 1990:2100
    data = webread(sprintf('https://urlaubstage-planen.de/feiertage-in-sachsen-%i-sn.htm', year));
    base = htmlTree(data);
    content = base.findElement('Article');
    holydayList = content.findElement('LI');
    snPublicHolidays = holydayList(1:nFreeDays);  % only work free days
    snPublicHolidays = split(snPublicHolidays.string, ' <EM>');
    snPublicHolidays = snPublicHolidays(:,1);
    snPublicHolidays = split(snPublicHolidays.string, '<LI>');
    snPublicHolidays = snPublicHolidays(:,2);
    snPublicHolidays = split(snPublicHolidays.string, ' - ');
    holydaysSN.date(idxStart:idxStop) = datetime(snPublicHolidays(:,1));
    holydaysSN.description(idxStart:idxStop) = datetime(snPublicHolidays(:,2));
    idxStart = idxStop + 1;
    idxStop = idxStop + nFreeDays;
end