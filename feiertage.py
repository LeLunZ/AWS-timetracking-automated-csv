import pickle
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

allg_feiertage = []

months = {
    'Jan': 1,
    'Feb': 2,
    'Mär': 3,
    'Apr': 4,
    'Mai': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Okt': 10,
    'Nov': 11,
    'Dez': 12
}


def load_allg_feiertage(start_date_time, end_date_time):
    years = set(
        [start_date_time.date().year + i for i in range(end_date_time.date().year - start_date_time.date().year + 1)])

    global allg_feiertage
    feier_f = Path('data/feiertage.pickle')
    if feier_f.is_file():
        with open(feier_f, 'rb') as f:
            allg_feiertage = pickle.load(f)
        distinct_years = set([f.year for f in allg_feiertage])
        if all(x in distinct_years for x in years):
            return

    driver = webdriver.Chrome('./chromedriver')
    for year in years:
        driver.get('https://www.timeanddate.de/feiertage/oesterreich/' + str(year) + '?hol=1')
        WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.XPATH, '//*/tbody')))
        try:
            cookie_ok = driver.find_element(By.XPATH,
                                            "//*/button[contains(@mode, 'primary') and contains(text(), 'ZUSTIMMEN')]")

            cookie_ok.click()
        except EC.NoSuchElementException:
            pass
        elements = driver.find_elements(By.XPATH, "//*/tbody/tr[@class='showrow']/th")

        for f in elements:
            f_split = f.text.split(' ')
            day = int(f_split[0].replace('.', ''))
            month = f_split[1]
            year = year
            allg_feiertage.append(datetime(year, months[month], day).date())
    with open(feier_f, 'wb') as f:
        pickle.dump(allg_feiertage, f)
    driver.quit()
