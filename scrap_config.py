# keyword file must be csv
# 'keyword' column must be present in the csv file (case does not matter)
keyword_file_path = r"domains-to-process\pending.csv"
done_keywords_csv_path = r"donekeywords\done_keywords.csv"
domain_extentions = ["nu", "com", "net", "dk"]
#domain_extentions = ["dk"]
keep_record_of_keywords = True
exclude_done_keywords = False
drive_path = r"drive\chromedriver"
api_key = "LXjGYlJ6w3aVrCgNFIhdPeUQ"
api_name = "synergy"
taken_status=0
available_status=1
unknown_status=2
exception_status=-1