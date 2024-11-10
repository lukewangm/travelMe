from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib

driver = webdriver.Chrome() # or webdriver.Firefox()

search_query = "search something"

driver.get(f"https://www.google.com/maps/search/{urllib.parse.quote(search_query)}/")

google_consent_button = driver.find_element(by=By.XPATH, value="/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[1]/div/div/button")
google_consent_button.click()

try:
    container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]')))
    search_results = container.find_elements(by=By.CSS_SELECTOR, value="*")
    
    for i in range(3, len(search_results),2):
           if search_results[i].get_attribute("class") != "TFQHme ":
               print(search_results[i].text)
finally:
    driver.quit()