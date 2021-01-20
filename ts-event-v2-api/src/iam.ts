import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from "axios";
import jwt_decode from 'jwt-decode';
const iamTokenPath = '/iam/v1.0/token';

function getIamTokenEndpoint(server: string ) {
    return server + iamTokenPath;
}


/**
 * Gets an IAM token using client credentials grant
 * @param clientId : The IAM client id for generating the token
 * @param clientSecret : The IAM client secret for generating the token
 * @param scope ; Scope required for the token
 * @param server : The IAM server url that generates the token 
 */
export const getToken = async (clientId: string , clientSecret : string, scope : string, server : string) : Promise<string> => {    
    let iam = getIamTokenEndpoint(server);
    let response = await axios.get(iam, {
        auth : {
            username : clientId,
            password : clientSecret
        },
        params : {
            grant_type : "client_credentials",
            scope : scope
        }
    })
    return response.data["access_token"];
}

/**
 * Gets an IAM token using resource owner password grant. This should be used for testing purpises only and NEVER in production
 */
export const getRopg = async (user : string, password : string, clientId : string , scope: string, server: string) => {
    let iam = getIamTokenEndpoint(server);
    const params = new URLSearchParams();
    params.append('grant_type', 'password');
    params.append('username', user);
    params.append('password', password);    
    params.append('client_id',clientId);
    params.append('scope' ,scope);
    console.log(`Ropg`);
    let response = await axios.post(iam , params, {  headers: { 'content-type': 'application/x-www-form-urlencoded' }}); 
    return response.data.access_token;
}

/**
 * Checks whether a given IAM token is valid or expired. 
 * @param token 
 */
export const expired = async( token : string) => {
    if (! token) return true;
    let d = jwt_decode(token) as any;
    let result = d['exp'] <=  Math.round(new Date().getTime() / 1000) ;
    return result;
}

