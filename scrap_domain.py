import time
from datetime import datetime
from concurrent import futures
from pandas import DataFrame, read_csv, concat, merge
import scrap_config
import os
import requests
import logging

result_list = []


def initiate_log():
    try:
        if os.path.isdir("log") == False:
            os.makedirs("log")
        LOG_FILENAME = datetime.now().strftime("./log/%d-%m-%Y.log")
        logging.basicConfig(
            level=logging.DEBUG,
            filename=LOG_FILENAME,
            format="%(asctime)s %(levelname)s:%(message)s",
        )
        if os.path.isfile(LOG_FILENAME) != True:
            logging.FileHandler(LOG_FILENAME, mode="w", encoding=None, delay=False)
    except Exception as e:
        print(f"Exception-(initiate_log)->{e}")


def handle_log(exception_data, method_name, *args):
    initiate_log()
    date_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    logging.exception(f"======Exception Start-->{date_time}============")
    logging.exception(f"Exception occurred! Method : {method_name}")
    logging.exception(f"Exception-->{exception_data}")
    if args:
        for data in args:
            logging.exception(f"Exception args-->{data}")
    logging.exception(f"===========END============")


def read_csv_from_path(path):
    try:
        # if the csv file is empty then return empty dataframe object
        if os.stat(rf"{path}").st_size == 0:
            return DataFrame()
        return read_csv(rf"{path}")
    except Exception as e:
        print("Exception in (exclude_checked_keywords)-->", e)
        handle_log(e, "exclude_checked_keywords")


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
        handle_log(e, "new_keywords_set")


def update_done_keyword_csv(df: DataFrame):
    try:
        df = df[["keyword", "checking_date"]]
        base_df = read_csv_from_path(scrap_config.done_keywords_csv_path)
        base_df = concat([base_df, df])
        base_df = base_df.drop_duplicates(subset=["keyword"])
        base_df.to_csv(scrap_config.done_keywords_csv_path, index=False)
    except Exception as e:
        print("Exception in (update_done_keyword_csv)-->", e)
        handle_log(e, "update_done_keyword_csv")


def save_result(source_df):
    try:
        final_df = DataFrame(result_list)
        source_df.columns = map(str.lower, source_df.columns)
        source_df.keyword = [x.replace(" ", "") for x in source_df.keyword]
        final_df = merge(source_df, final_df, on=["keyword"], how="inner")
        file_path_report=scrap_config.keyword_file_path
        file_path_report=file_path_report.replace(".csv","_Report")
        final_df.to_csv(rf"{file_path_report}.csv", index=False)
        if scrap_config.keep_record_of_keywords:
            update_done_keyword_csv(final_df)
    except Exception as e:
        print("Exception in (save_result)-->", e)
        handle_log(e, "save_result")


def is_english_word(s):
    try:
        s.encode(encoding="utf-8").decode("ascii")
    except UnicodeDecodeError:
        pass
    else:
        s = s.replace(" ", "")
        if not any(not c.isalnum() for c in s):
            return s


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
        return keywords_list
    except Exception as e:
        print("Exception in (prepare_keyword_list)-->", e)
        handle_log(e, "prepare_keyword_list")


def check_domain_availability_api(keywords_list):
    try:
        global domain_extentions
        global result_list
        # for keyword in keywords_list:
        keyword = keywords_list
        result_dict = {"keyword": keyword}
        for extention in scrap_config.domain_extentions:
            try:
                full_domain = f"{keyword}.{extention}"
                url = f"https://api.simply.com/2/my/domaincheck/{full_domain}"
                response = requests.get(
                    url,
                    auth=(scrap_config.api_name, scrap_config.api_key),
                )
                if response.json()["domain"]["status"] == "taken":
                    result_dict[extention] = scrap_config.taken_status
                elif response.json()["domain"]["status"] == "available":
                    result_dict[extention] = scrap_config.available_status
                else:
                    result_dict[extention] = scrap_config.unknown_status
                print(full_domain, "---> Status: ", response.json()["domain"]["status"]," Code: ",result_dict[extention])
            except Exception as e:
                result_dict[extention] = scrap_config.exception_status
                handle_log(e, "check_domain_availability_api_loop(extentions)", url)
                print("===Exception in (check_domain_availability_api) loop-->", e)
                print("URL--->", url)
                print("===================")
        result_dict["checking_date"] = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        result_list.append(result_dict)
    except Exception as e:
        print("Exception in (check_domain_availability_api)-->", e)
        handle_log(e, "check_domain_availability_api")


if __name__ == "__main__":
    try:
        df = read_csv(scrap_config.keyword_file_path, encoding="latin1")
        list_of_keywords = prepare_keyword_list(df)
        print("Number of list in lists_of_keyword-->", len(list_of_keywords))
        if len(list_of_keywords) > 0:
            t0 = time.time()
            print("Starting Threads to get domain information")
            with futures.ThreadPoolExecutor() as executor:  # default/optimized number of threads
                titles = list(
                    executor.map(check_domain_availability_api, list_of_keywords)
                )
                save_result(df)
            print("Time Taken-->", (time.time() - t0) / 60, "MINUTES")
    except Exception as e:
        print("Exception in (__main__)-->", e)
        handle_log(e, "__main__")
