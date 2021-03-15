#!/usr/bin/env node
import yargs = require('yargs');
import {getToken, expired} from './iam';
import axios from "axios";
import { start } from 'repl';
import { time } from 'console';


// We will set these globals via the command line
let clientId : string ;
let clientSecret : string ;
let scope : string = 'epo.evt.r';
let apiKey : string ;
let iamServer : string = 'https://iam.mcafee-cloud.com';
let token : string;
let period : number;
let endpoint : string = 'https://api.mvision.mcafee.com';
let timestamp : string = ''

const fetchToken = async (current : string) => {
    let isExpired : boolean = await expired(current);
    if (! isExpired) return current;
    return getToken(clientId, clientSecret, scope,iamServer)
 }

/**
 * @param startTime Start time from which to fetch events * 
 */

const pollEvents = async (startTime : Date) => {
    try{
        let url = endpoint + "/epo/v2/events";   
        let next = null;
        let hasMore = true;

        while (hasMore){
            token  = await fetchToken(token);     
            console.log(`Fetching threat events from MVISION epo`);
            let params : any = {
                'filter[timestamp][GE]' : startTime.toISOString(),
                'page[limit]' : 1000
            }
            if (next) {
                url = next;
                params = {}
            }

            let response = await axios.get(url, { 
                headers : { 
                    authorization : `Bearer ${token}`,
                    'x-api-key' : apiKey,
                    'content-type' : 'application/vnd.api+json'
                },
                params
            });
            
            next = response?.data?.links?.next
            hasMore = next!=null
            let eventIds = response.data.data.map((x: any) => x.id)
            console.log(eventIds)
            console.log(`${next}`)
        }        
    }catch(err) {
        console.log(`Error getting events from ePO ${err}`);
    }finally {
        // Set up the next invokation after period milliseconds
        let date = new Date()
        setTimeout(pollEvents.bind(null,date),period);
    }
}



const main = async () => {
   const argv = yargs.options({
       c: { type: 'string', alias: 'clientid',demandOption : true, describe : 'client id (if using client credentials) or  username (if using ropg)' },  
       s: { type: 'string', alias: 'secret',demandOption : true, describe : 'client secret (if using client credentials) or  password (if using ropg)' },  
       p: { type: 'number',alias: 'period', demandOption: false, describe : 'poll internal in seconds'},
       d: { type: 'string', alias: 'timestamp', demandOption: true, describe : 'Starting time value in ISO format, e.g. 2021-01-19T12:00:00'},
       k: { type: 'string', alias: 'api key', demandOption: true, describe : 'api key'}
   })
   .argv;

   clientId = argv.c;
   clientSecret = argv.s;
   period = argv.p ? argv.p * 1000 : 300000; // Default 5 minute interval
   timestamp = argv.d   
   apiKey = argv.k
    // Start with an initial start point of 
   pollEvents( new Date(timestamp));

}

main()
