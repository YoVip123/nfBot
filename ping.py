import requests

url = "https://nfbot.onrender.com"

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
  'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
  'Accept-Encoding': "gzip, deflate, br, zstd",
  'sec-ch-ua': "\"Google Chrome\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
  'sec-ch-ua-mobile': "?1",
  'sec-ch-ua-platform': "\"Android\"",
  'upgrade-insecure-requests': "1",
  'sec-fetch-site': "cross-site",
  'sec-fetch-mode': "navigate",
  'sec-fetch-user': "?1",
  'sec-fetch-dest': "document",
  'accept-language': "en-US,en;q=0.9,hi;q=0.8",
  'priority': "u=0, i"
}

response = requests.get(url, headers=headers)

print(response.text)
