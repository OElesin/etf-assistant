import requests
import json
import math
import time
import urllib.parse

url = "https://www.justetf.com/en/search.html"
params = {
    "4-1.0-container-tabsContentContainer-tabsContentRepeater-1-container-content-etfsTablePanel": "",
    "search": "ETFS",
    "_wicket": "1"
}

headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.justetf.com",
    "priority": "u=1, i",
    "referer": "https://www.justetf.com/en/search.html?search=ETFS",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "cookie": "XSRF-TOKEN=556869fa-f175-4e87-b5f5-c825298ab805; JSESSIONID=27E5AD8DCF0FE98B46CCE50FE54F9181; locale_=en; _vwo_consent=1%2C1%3A~; _ga=GA1.1.1670669208.1770718025; _gcl_au=1.1.412228076.1770718025; FPID=FPID2.2.rl5QMmms0lWBipIAtEvbJlfknciCf37BTxs%2FNwh1Shc%3D.1770718025; FPLC=g7B1zLzr4iDOSezN7zi0oo%2B9cQrmAFWRpY9wsLPi1Ljb3idq6JENhe9WPaGkKVDuv5owUumtbfhz96DEdtfxX2FRVxVzZPdDte3bToj2BQ%2FTAQP2OnczmsXeVzuHJg%3D%3D; _vwo_uuid_v2=DAC66E64599271A72D9C235A11040BCD3|2ee48862493b2d39b83e9ae925136519; _vwo_uuid=DAC66E64599271A72D9C235A11040BCD3; _vwo_ds=3%241770718029%3A85.42504918%3A%3A%3A%3A%3A1770718029%3A1770718029%3A1; _vis_opt_s=1%7C; _vis_opt_test_cookie=1; _vwo_sn=0%3A3%3A%3A%3A%3A%3A49; etfs-search-order=fundSize%2Cdesc; _ga_EVC01HL6ZH=GS2.1.s1770718024$o1$g1$t1770718086$j59$l0$h1544920328; AWSALB=F7ueYKuBRzQskfxi5GAO+frIwElARFukNl4sYq9YQ4AO4ceOROn6bQRsqnMVDRxfXX97b2uqvRrS0lIMGa9/y4mq7kMwDnU5l7EeiG7Q/YOh3J7fZSB6yssB7WE9; AWSALBCORS=F7ueYKuBRzQskfxi5GAO+frIwElARFukNl4sYq9YQ4AO4ceOROn6bQRsqnMVDRxfXX97b2uqvRrS0lIMGa9/y4mq7kMwDnU5l7EeiG7Q/YOh3J7fZSB6yssB7WE9"
}

# The initial payload string
data_str = "draw=2&columns%5B0%5D%5Bdata%5D=&columns%5B0%5D%5Bname%5D=selectCheckbox&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=name&columns%5B1%5D%5Bname%5D=name&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=&columns%5B2%5D%5Bname%5D=sparkline&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=false&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=fundCurrency&columns%5B3%5D%5Bname%5D=fundCurrency&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=fundSize&columns%5B4%5D%5Bname%5D=fundSize&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=ter&columns%5B5%5D%5Bname%5D=ter&columns%5B5%5D%5Bsearchable%5D=true&columns%5B5%5D%5Borderable%5D=true&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=&columns%5B6%5D%5Bname%5D=bullet&columns%5B6%5D%5Bsearchable%5D=true&columns%5B6%5D%5Borderable%5D=false&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata%5D=weekReturnCUR&columns%5B7%5D%5Bname%5D=weekReturn&columns%5B7%5D%5Bsearchable%5D=true&columns%5B7%5D%5Borderable%5D=true&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bdata%5D=monthReturnCUR&columns%5B8%5D%5Bname%5D=monthReturn&columns%5B8%5D%5Bsearchable%5D=true&columns%5B8%5D%5Borderable%5D=true&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bdata%5D=threeMonthReturnCUR&columns%5B9%5D%5Bname%5D=threeMonthReturn&columns%5B9%5D%5Bsearchable%5D=true&columns%5B9%5D%5Borderable%5D=true&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bdata%5D=sixMonthReturnCUR&columns%5B10%5D%5Bname%5D=sixMonthReturn&columns%5B10%5D%5Bsearchable%5D=true&columns%5B10%5D%5Borderable%5D=true&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B11%5D%5Bdata%5D=yearReturnCUR&columns%5B11%5D%5Bname%5D=yearReturn&columns%5B11%5D%5Bsearchable%5D=true&columns%5B11%5D%5Borderable%5D=true&columns%5B11%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B11%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B12%5D%5Bdata%5D=threeYearReturnCUR&columns%5B12%5D%5Bname%5D=threeYearReturn&columns%5B12%5D%5Bsearchable%5D=true&columns%5B12%5D%5Borderable%5D=true&columns%5B12%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B12%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B13%5D%5Bdata%5D=fiveYearReturnCUR&columns%5B13%5D%5Bname%5D=fiveYearReturn&columns%5B13%5D%5Bsearchable%5D=true&columns%5B13%5D%5Borderable%5D=true&columns%5B13%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B13%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B14%5D%5Bdata%5D=ytdReturnCUR&columns%5B14%5D%5Bname%5D=ytdReturn&columns%5B14%5D%5Bsearchable%5D=true&columns%5B14%5D%5Borderable%5D=true&columns%5B14%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B14%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B15%5D%5Bdata%5D=yearReturn1CUR&columns%5B15%5D%5Bname%5D=yearReturn1&columns%5B15%5D%5Bsearchable%5D=true&columns%5B15%5D%5Borderable%5D=true&columns%5B15%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B15%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B16%5D%5Bdata%5D=yearReturn2CUR&columns%5B16%5D%5Bname%5D=yearReturn2&columns%5B16%5D%5Bsearchable%5D=true&columns%5B16%5D%5Borderable%5D=true&columns%5B16%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B16%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B17%5D%5Bdata%5D=yearReturn3CUR&columns%5B17%5D%5Bname%5D=yearReturn3&columns%5B17%5D%5Bsearchable%5D=true&columns%5B17%5D%5Borderable%5D=true&columns%5B17%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B17%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B18%5D%5Bdata%5D=yearReturn4CUR&columns%5B18%5D%5Bname%5D=yearReturn4&columns%5B18%5D%5Bsearchable%5D=true&columns%5B18%5D%5Borderable%5D=true&columns%5B18%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B18%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B19%5D%5Bdata%5D=yearVolatilityCUR&columns%5B19%5D%5Bname%5D=yearVolatility&columns%5B19%5D%5Bsearchable%5D=true&columns%5B19%5D%5Borderable%5D=true&columns%5B19%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B19%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B20%5D%5Bdata%5D=threeYearVolatilityCUR&columns%5B20%5D%5Bname%5D=threeYearVolatility&columns%5B20%5D%5Bsearchable%5D=true&columns%5B20%5D%5Borderable%5D=true&columns%5B20%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B20%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B21%5D%5Bdata%5D=fiveYearVolatilityCUR&columns%5B21%5D%5Bname%5D=fiveYearVolatility&columns%5B21%5D%5Bsearchable%5D=true&columns%5B21%5D%5Borderable%5D=true&columns%5B21%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B21%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B22%5D%5Bdata%5D=yearReturnPerRiskCUR&columns%5B22%5D%5Bname%5D=yearReturnPerRisk&columns%5B22%5D%5Bsearchable%5D=true&columns%5B22%5D%5Borderable%5D=true&columns%5B22%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B22%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B23%5D%5Bdata%5D=threeYearReturnPerRiskCUR&columns%5B23%5D%5Bname%5D=threeYearReturnPerRisk&columns%5B23%5D%5Bsearchable%5D=true&columns%5B23%5D%5Borderable%5D=true&columns%5B23%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B23%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B24%5D%5Bdata%5D=fiveYearReturnPerRiskCUR&columns%5B24%5D%5Bname%5D=fiveYearReturnPerRisk&columns%5B24%5D%5Bsearchable%5D=true&columns%5B24%5D%5Borderable%5D=true&columns%5B24%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B24%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B25%5D%5Bdata%5D=yearMaxDrawdownCUR&columns%5B25%5D%5Bname%5D=yearMaxDrawdown&columns%5B25%5D%5Bsearchable%5D=true&columns%5B25%5D%5Borderable%5D=true&columns%5B25%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B25%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B26%5D%5Bdata%5D=threeYearMaxDrawdownCUR&columns%5B26%5D%5Bname%5D=threeYearMaxDrawdown&columns%5B26%5D%5Bsearchable%5D=true&columns%5B26%5D%5Borderable%5D=true&columns%5B26%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B26%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B27%5D%5Bdata%5D=fiveYearMaxDrawdownCUR&columns%5B27%5D%5Bname%5D=fiveYearMaxDrawdown&columns%5B27%5D%5Bsearchable%5D=true&columns%5B27%5D%5Borderable%5D=true&columns%5B27%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B27%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B28%5D%5Bdata%5D=maxDrawdownCUR&columns%5B28%5D%5Bname%5D=maxDrawdown&columns%5B28%5D%5Bsearchable%5D=true&columns%5B28%5D%5Borderable%5D=true&columns%5B28%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B28%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B29%5D%5Bdata%5D=inceptionDate&columns%5B29%5D%5Bname%5D=inceptionDate&columns%5B29%5D%5Bsearchable%5D=true&columns%5B29%5D%5Borderable%5D=true&columns%5B29%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B29%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B30%5D%5Bdata%5D=distributionPolicy&columns%5B30%5D%5Bname%5D=distributionPolicy&columns%5B30%5D%5Bsearchable%5D=true&columns%5B30%5D%5Borderable%5D=false&columns%5B30%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B30%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B31%5D%5Bdata%5D=sustainable&columns%5B31%5D%5Bname%5D=sustainable&columns%5B31%5D%5Bsearchable%5D=true&columns%5B31%5D%5Borderable%5D=true&columns%5B31%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B31%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B32%5D%5Bdata%5D=numberOfHoldings&columns%5B32%5D%5Bname%5D=numberOfHoldings&columns%5B32%5D%5Bsearchable%5D=true&columns%5B32%5D%5Borderable%5D=true&columns%5B32%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B32%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B33%5D%5Bdata%5D=currentDividendYield&columns%5B33%5D%5Bname%5D=currentDividendYield&columns%5B33%5D%5Bsearchable%5D=true&columns%5B33%5D%5Borderable%5D=true&columns%5B33%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B33%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B34%5D%5Bdata%5D=yearDividendYield&columns%5B34%5D%5Bname%5D=yearDividendYield&columns%5B34%5D%5Bsearchable%5D=true&columns%5B34%5D%5Borderable%5D=true&columns%5B34%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B34%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B35%5D%5Bdata%5D=domicileCountry&columns%5B35%5D%5Bname%5D=domicileCountry&columns%5B35%5D%5Bsearchable%5D=true&columns%5B35%5D%5Borderable%5D=false&columns%5B35%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B35%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B36%5D%5Bdata%5D=replicationMethod&columns%5B36%5D%5Bname%5D=replicationMethod&columns%5B36%5D%5Bsearchable%5D=true&columns%5B36%5D%5Borderable%5D=false&columns%5B36%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B36%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B37%5D%5Bdata%5D=savingsPlanReady&columns%5B37%5D%5Bname%5D=savingsPlanReady&columns%5B37%5D%5Bsearchable%5D=true&columns%5B37%5D%5Borderable%5D=false&columns%5B37%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B37%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B38%5D%5Bdata%5D=hasSecuritiesLending&columns%5B38%5D%5Bname%5D=hasSecuritiesLending&columns%5B38%5D%5Bsearchable%5D=true&columns%5B38%5D%5Borderable%5D=false&columns%5B38%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B38%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B39%5D%5Bdata%5D=isin&columns%5B39%5D%5Bname%5D=isin&columns%5B39%5D%5Bsearchable%5D=true&columns%5B39%5D%5Borderable%5D=false&columns%5B39%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B39%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B40%5D%5Bdata%5D=ticker&columns%5B40%5D%5Bname%5D=ticker&columns%5B40%5D%5Bsearchable%5D=true&columns%5B40%5D%5Borderable%5D=false&columns%5B40%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B40%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B41%5D%5Bdata%5D=wkn&columns%5B41%5D%5Bname%5D=wkn&columns%5B41%5D%5Bsearchable%5D=true&columns%5B41%5D%5Borderable%5D=false&columns%5B41%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B41%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B42%5D%5Bdata%5D=valorNumber&columns%5B42%5D%5Bname%5D=valorNumber&columns%5B42%5D%5Bsearchable%5D=true&columns%5B42%5D%5Borderable%5D=false&columns%5B42%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B42%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B43%5D%5Bdata%5D=&columns%5B43%5D%5Bname%5D=addButton&columns%5B43%5D%5Bsearchable%5D=true&columns%5B43%5D%5Borderable%5D=false&columns%5B43%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B43%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=4&order%5B0%5D%5Bdir%5D=desc&start=25&length=25&search%5Bvalue%5D=&search%5Bregex%5D=false&ajaxsortOrder=desc&ajaxsortField=fundSize&lang=en&country=DE&defaultCurrency=EUR&universeType=private&etfsParams=search%3DETFS%26query%3D"

# Convert the form-urlencoded string to a dict so we can modify it
parsed_data = urllib.parse.parse_qs(data_str)
payload_dict = {k: v[0] for k, v in parsed_data.items()}

try:
    response = requests.post(url, params=params, headers=headers, data=payload_dict)
    response.raise_for_status()
    print(f"Status Code: {response.status_code}")
    
    # Parse the response
    data_json = response.json()
    total_records = data_json.get("recordsTotal", 0)
    print(f"Total records found: {total_records}")
    
    all_etfs = []
    
    # Calculate number of pages needed
    # (Total records / page size) rounded up
    page_size = 25
    num_pages = math.ceil(total_records / page_size)
    
    # Iterate through all pages
    for page in range(num_pages):
        start_index = page * page_size
        print(f"Fetching page {page + 1}/{num_pages} (start index: {start_index})...")
        
        # Update the start index in the payload
        current_data = payload_dict.copy()
        current_data['start'] = start_index
        current_data['draw'] = page + 1
        
        response = requests.post(url, params=params, headers=headers, data=current_data)
        response.raise_for_status()
        
        page_data = response.json()
        etfs = page_data.get("data", [])
        all_etfs.extend(etfs)
        
        # Be nice to the server
        time.sleep(0.5)

    # Save all collected data
    final_output = {
        "recordsTotal": total_records,
        "recordsFiltered": total_records, 
        "data": all_etfs
    }
    
    with open('output.json', 'w') as f:
        json.dump(final_output, f, indent=4)
        
    print(f"Successfully fetched {len(all_etfs)} ETFs and saved to output.json")
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
