This is a typescript project to use the v2 event apis. When using event apis, I have found the following strategy helpful

If you need to import all your mvision threat events to some other external store, and continue to pull new events recurringly then you should have a 3 step strategy

1. Import all events from epoch to midnight today/yesterday
2. Import all events from 00:00:00 todays date to "nearest elapsed round hour from now". For example it its 5:20 PM, then this time stamp could be 17:00:00
3. Import all events from 17:00:00 to current time, and then start a loop to run every 5 minutes to pick up last 5 minutes worth of events. YMMV depending on the volume of traffic you actually process

The sample takes in a timestamp (a starting point), and fetches all event from the timestamp to current time, and then poll periodically to consume any new events 
