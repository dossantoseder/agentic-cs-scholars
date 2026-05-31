import requests
from bs4 import BeautifulSoup

url = "http://plsql1.cnpq.br/divulg/RESULTADO_PQ_102003.prc_comp_cmt_links?V_COD_DEMANDA=200310&V_TPO_RESULT=CURSO&V_COD_AREA_CONHEC=10300007&V_COD_CMT_ASSESSOR=CC"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
}

print(f"Fetching: {url}\n")

response = requests.get(url, headers=headers, timeout=30)
print(f"Status Code: {response.status_code}")
print(f"Content Length: {len(response.text)}")
print(f"First 2000 characters:\n")
print(response.text[:2000])

soup = BeautifulSoup(response.text, "lxml")
print(f"\n\n--- HTML Analysis ---")
print(f"Tables found: {len(soup.find_all('table'))}")
print(f"Divs found: {len(soup.find_all('div'))}")
print(f"Forms found: {len(soup.find_all('form'))}")

for i, table in enumerate(soup.find_all('table')):
    print(f"\nTable {i}: {len(table.find_all('tr'))} rows")
