from msu_ssc import ssc_log

if __name__ == "__main__":
    import sys
    from pprint import pprint

    pprint(sys.path)
    print(ssc_log)
    ssc_log.init(
        level="DEBUG",
        file_path="./logs/test.log",
    )
