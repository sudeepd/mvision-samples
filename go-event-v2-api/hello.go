package main
import(
	"net/http"
	"io/ioutil"
	"fmt"
	"time"
	"encoding/json"
	"github.com/dgrijalva/jwt-go"
	"strconv"
)

type Token struct {
	Type string `json:"token_type"`
	Expires int `json:"expires"`
	AccessToken string `json:"access_token"`

}

func IsExpired(tokenString string) bool{	
	fmt.Println("Checking token expiry ")
	token, _ ,err:= new(jwt.Parser).ParseUnverified(tokenString, jwt.MapClaims{})
	if err != nil {
		fmt.Println("Invalid token")
        fmt.Println(err)
        return true
    }

    if claims, ok := token.Claims.(jwt.MapClaims); ok {		
		var expiry int64 = int64(claims["exp"].(float64))
		if (expiry < time.Now().UnixNano() / int64(time.Millisecond)) {
			return true
		}

    } else {
		fmt.Println(err)
		return true
	}
	return false
}

func GetToken(current string ,clientId string, clientSecret string, scope string, server string ) string{
	fmt.Println("Creating new token")
	if (! IsExpired(current)) {
		return current
	}
	var endpoint string = server + "/iam/v1.0/token"
    client := &http.Client{}
	req,err := http.NewRequest("GET",endpoint, nil)
	q := req.URL.Query()
	q.Add("grant_type", "client_credentials")
	q.Add("scope", scope)
	req.SetBasicAuth(clientId, clientSecret)
	req.URL.RawQuery = q.Encode()
	resp, err := client.Do(req)

	body, err := ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	var token Token
	json.Unmarshal(body, &token)
	if (err != nil) {
		fmt.Printf("%s", err)
	}
	fmt.Println("Creating new token")
	return token.AccessToken
}


/**
Fetches events in a given time window, given start and end. If end is in future the end argument is 
omitted from the query param
*/
func fetchEvents(startTime string, 
	endTime string,
	clientId string , 	
	clientSecret string,
	scope string,
	iam string,
	apiKey string) {
		var token = ""
		var url = "https://api.mvision.mcafee.com/epo/v2/events"
		var next *string = nil
		var hasMore = true 
		for hasMore {
			if ( next != nil) {
				url = *next
			}

			token = GetToken(token,clientId, clientSecret, scope, iam)
			fmt.Println(token)
			fmt.Println(url)
			client := &http.Client{}
			req,err := http.NewRequest("GET", url, nil)
			var authHeader string = "Bearer " + token
			q := req.URL.Query()
			if (next == nil) {
				q.Add("filter[timestamp][GE]", startTime)
				q.Add("filter[timestamp][LE]", endTime)
			} 
			q.Add("page[limit]", strconv.Itoa(10))
			
			req.Header.Add("Authorization", authHeader)
			req.Header.Add("Content-Type","application/vnd.api+json")
			req.Header.Add("x-api-key",apiKey)

			fmt.Println("Invoking request to get events")
			req.URL.RawQuery = q.Encode()
			resp, err := client.Do(req)
		
			if (err != nil) {
				fmt.Printf("%s",err)
			}
			
			body, err := ioutil.ReadAll(resp.Body)
			resp.Body.Close()

			if (err != nil) {
				fmt.Printf("Printing error body")
				fmt.Printf("%s",err)
			}else {
				fmt.Println("Printing response body ", string(body))				
			}
			hasMore = false		
		}
}


func main() {
	var start string = "2021-01-21T00:00:00.000"
	var end string = "2021-01-21T06:00:00.000"
	var clientId string = ""
	var clientSecret string = ""
	var scope string = "epo.evt.r"
	var iam = "https://iam.mcafee-cloud.com"
	var apiKey = ""

	fetchEvents(start, end, clientId, clientSecret,scope, iam, apiKey)
}