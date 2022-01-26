from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
from concurrent import futures
from pandas import DataFrame, read_csv, concat
import scrap_config

result_list = []


def exclude_checked_keywords(new_keywords_set):
    try:
        print("Excluding already checked keywords")
        print("New Word List Length-->", len(new_keywords_set))
        done_keywords_df = read_csv(scrap_config.done_keywords_csv_path)
        done_keywords_df.columns = map(str.lower, done_keywords_df.columns)
        checked_keyword_set = set(list(done_keywords_df.keyword))
        remaining_keywords_list = list(new_keywords_set - checked_keyword_set)
        print("Number of checked keywords->", len(checked_keyword_set))
        print("Number of unchecked keywords->", len(remaining_keywords_list))
        return remaining_keywords_list
    except Exception as e:
        print("Exception in (exclude_checked_keywords)-->", e)


def update_done_keyword_csv(df: DataFrame):
    try:
        df = df[["keyword", "checking_date"]]
        base_df = read_csv(scrap_config.done_keywords_csv_path)
        base_df = concat([base_df, df])
        base_df = base_df.drop_duplicates(subset=["keyword"])
        base_df.to_csv(scrap_config.done_keywords_csv_path, index=False)
    except Exception as e:
        print("Exception in (update_done_keyword_csv)-->", e)


def save_result():
    try:
        final_df = DataFrame(result_list)
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"report_{date}"
        final_df.to_csv(f"{file_name}.csv", index=False)
        if scrap_config.keep_record_of_keywords:
            update_done_keyword_csv(final_df)
    except Exception as e:
        print("Exception in (save_result)-->", e)


def get_driver():
    try:
        url = "https://www.simply.com/en/"
        driver = Chrome(
            executable_path=r"/home/rifat/Documents/interview/domain_scraping/driver/chromedriver"
        )
        driver.get(url)
        return driver
    except Exception as e:
        print("Exception in (get_driver)-->", e)


def is_english_word(s):
    try:
        s.encode(encoding="utf-8").decode("ascii")
    except UnicodeDecodeError:
        pass
    else:
        return s.replace(" ", "")


def prepare_keyword_list(df: DataFrame):
    try:
        df.columns = map(str.lower, df.columns)
        keywords = list(df.keyword)
        # taking the only english words and making set to erase duplicates
        keywords_set = set(map(is_english_word, keywords))
        if None in keywords_set:
            keywords_set.remove(None)
        # if exclusion of already checked keywords is needed
        if scrap_config.exclude_done_keywords:
            keywords_list = exclude_checked_keywords(keywords_set)
        else:
            keywords_list = list(keywords_set)
        # making lists of list of keywords (each list will contain {num_of_lists} number of keywords)
        num_of_lists = 20
        lists_of_keywords = [
            keywords_list[x : x + num_of_lists]
            for x in range(0, len(keywords_list), num_of_lists)
        ]
        return lists_of_keywords
    except Exception as e:
        print("Exception in (prepare_keyword_list)-->", e)


def check_domain_availability(keywords_list):
    try:
        global domain_extentions
        global result_list
        driver = get_driver()
        is_first_load = False
        for keyword in keywords_list:
            result_dict = {"keyword": keyword}
            for extention in scrap_config.domain_extentions:
                try:
                    full_domain = f"{keyword}.{extention}"
                    inputElement = driver.find_element_by_class_name("form-control")
                    if not is_first_load:
                        inputElement.send_keys(Keys.CONTROL + "a")
                        inputElement.send_keys(Keys.DELETE)
                    is_first_load = False
                    inputElement.send_keys(full_domain)
                    inputElement.send_keys(Keys.ENTER)
                    time.sleep(0.6)
                    elements = driver.find_elements_by_class_name("text-success")
                    text = elements[0].text
                    if "The domain you searched for is available!" in text:
                        result_dict[extention] = 1
                        # print(full_domain,"-->Domain Available")
                    else:
                        result_dict[extention] = 0
                        # print(full_domain,"-->Domain not available")

                    del elements
                except Exception as e:
                    result_dict[extention] = str(e)
                    print("Exception-->", e)
            result_dict["checking_date"] = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            result_list.append(result_dict)
        driver.quit()
    except Exception as e:
        print("Exception in (check_domain_availability)-->", e)


if __name__ == "__main__":
    df = read_csv(
        "google_dk__all-keywords_2022-01-23_11-32-06-2.csv", encoding="latin1"
    )
    lists_of_keywords = prepare_keyword_list(df)
    print("Number of list in lists_of_keyword-->", len(lists_of_keywords))
    if len(lists_of_keywords) > 0:
        t0 = time.time()
        print("Starting Threads to get domain information")
        with futures.ThreadPoolExecutor() as executor:  # default/optimized number of threads
            titles = list(executor.map(check_domain_availability, lists_of_keywords))
            save_result()
        print("Time Taken-->", (time.time() - t0) / 60, "MIN")
