%% Parameter
startTime = datetime("01.01.2020 00:00:00");
endTime = datetime("31.01.2020 23:45:00");

%% Init
time = startTime:minutes(15):endTime;
getNormSLPs(startTime, endTime);

agent = PHHconsumer_e();