package scraper

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// The direct JSON API for Petrolimex CMS that holds fuel prices.
// We pass a base64 encoded JSON filter via the 'x-request' parameter.
const petrolimexAPIUrl = "https://portals.petrolimex.com.vn/~apis/portals/cms.item/search?object-identity=search&x-request=eyJGaWx0ZXJCeSI6eyJBbmQiOlt7IlN5c3RlbUlEIjp7IkVxdWFscyI6IjY3ODNkYzEyNzFmZjQ0OWU5NWI3NGE5NTIwOTY0MTY5In19LHsiUmVwb3NpdG9yeUlEIjp7IkVxdWFscyI6ImE5NTQ1MWUyM2I0NzRmZTU4ODZiZmI3Y2Y4NDNmNTNjIn19LHsiUmVwb3NpdG9yeUVudGl0eUlEIjp7IkVxdWFscyI6IjM4MDEzNzhmZTFlMDQ1YjFhZmExMGRlN2M1Nzc2MTI0In19LHsiU3RhdHVzIjp7IkVxdWFscyI6IlB1Ymxpc2hlZCJ9fV19LCJTb3J0QnkiOnsiTGFzdE1vZGlmaWVkIjoiRGVzY2VuZGluZyJ9LCJQYWdpbmF0aW9uIjp7IlRvdGFsUmVjb3JkcyI6LTEsIlRvdGFsUGFnZXMiOjAsIlBhZ2VTaXplIjowLCJQYWdlTnVtYmVyIjowfX0="

// PetrolimexAPIResponse represents the JSON structure from Petrolimex API
type PetrolimexAPIResponse struct {
	Objects []struct {
		Title        string  `json:"Title"`
		Zone1Price   float64 `json:"Zone1Price"`
		Zone2Price   float64 `json:"Zone2Price"`
		LastModified string  `json:"LastModified"`
		OrderIndex   int     `json:"OrderIndex"`
	} `json:"Objects"`
}

// ScrapePetrolimex fetches the latest retail fuel prices directly from Petrolimex API.
func ScrapePetrolimex() PriceData {
	data := PriceData{
		Company: "Petrolimex",
	}

	req, err := http.NewRequest("GET", petrolimexAPIUrl, nil)
	if err != nil {
		data.Error = fmt.Sprintf("failed to create request: %v", err)
		return data
	}

	// Setup necessary headers to look like a normal browser request
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "application/json, text/plain, */*")
	req.Header.Set("Origin", "https://www.petrolimex.com.vn")
	req.Header.Set("Referer", "https://www.petrolimex.com.vn/")

	client := &http.Client{}
	res, err := client.Do(req)
	if err != nil {
		data.Error = fmt.Sprintf("failed to fetch: %v", err)
		return data
	}
	defer res.Body.Close()

	if res.StatusCode != 200 {
		data.Error = fmt.Sprintf("status code: %d", res.StatusCode)
		return data
	}

	var apiRes PetrolimexAPIResponse
	if err := json.NewDecoder(res.Body).Decode(&apiRes); err != nil {
		data.Error = fmt.Sprintf("failed to parse JSON: %v", err)
		return data
	}

	for _, item := range apiRes.Objects {
		// Only add items that have a price
		if item.Title != "" && item.Zone1Price > 0 {
			price1 := formatPrice(item.Zone1Price)
			price2 := formatPrice(item.Zone2Price)

			data.Prices = append(data.Prices, FuelPrice{
				Name:       item.Title,
				PriceZone1: price1,
				PriceZone2: price2,
			})

			// Set updated_at from the first item if not set
			if data.UpdatedAt == "" && item.LastModified != "" {
				data.UpdatedAt = item.LastModified
			}
		}
	}

	if len(data.Prices) == 0 {
		data.Error = "no prices extracted from API response"
	}

	return data
}

// formatPrice converts a float64 (e.g., 27040) into formatted string "27.040"
func formatPrice(price float64) string {
	intPrice := int(price)
	s := fmt.Sprintf("%d", intPrice)
	if len(s) > 3 {
		return s[:len(s)-3] + "." + s[len(s)-3:]
	}
	return s
}
