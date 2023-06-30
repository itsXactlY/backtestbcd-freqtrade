import json
import os
import glob
import argparse
import subprocess
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def split_into_chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def get_config_filename(timerange_start):
    month_before = timerange_start - timedelta(days=30)
    formatted_date = month_before.strftime("%Y%m%d")
    return f"\\freqtrade\\user_data\\pairlists\\binance_spot\\USDT\\daily\\daily_200_USDT_0,5_minprice_{formatted_date}.json" # windows folder formating

# Parse command line arguments
parser = argparse.ArgumentParser(description='Support backtest num_pair/total_pair once, different timeranges and output !')
parser.add_argument('-n', '--num_pairs', type=int, help='Number of pairs in each command')
parser.add_argument('-r', '--command', type=str, default='python3 backtestbcd.py -n 10 -r "freqtrade backtesting --strategy-list your_stra -c config_test.json --cache none --export signals --timeframe 1m --max-open-trades 3 --enable-protections"', help='Command to execute')
parser.add_argument('-tr', '--timerange', type=str, default="20230310-20230311 20230201-20230202 20220610-20220611 20230102-20230104 20230104-", help='Timerange')

args = parser.parse_args()

start_time = time.time()

if args.command is not None:
    command = args.command
    timerange = args.timerange

    # Split the command string and timerange string into parts
    parts = command.split()
    ranges = timerange.split()

    for a, range_str in enumerate(ranges):
        timerange_parts = range_str.split("-")
        timerange_start = datetime.strptime(timerange_parts[0], "%Y%m%d")
        config_filename = get_config_filename(timerange_start)

        with open(config_filename) as f:
            filtered_lines = [line for line in f if not line.strip().startswith("//")]
            filtered_content = ''.join(filtered_lines)
            data = json.loads(filtered_content)

        pair_whitelist = data['exchange']['pair_whitelist']
        if args.num_pairs is not None and args.num_pairs > 0:
            num_pair_one = args.num_pairs
            pair_test = list(split_into_chunks(pair_whitelist, num_pair_one))
            num_backtest = len(pair_test) * len(ranges)
            print(f"--> OK! Let's run {num_backtest} backtests, please wait....")
            for i, pairs in enumerate(pair_test):
                formatted_pairs = ' '.join(pairs)
                cmd = f"{command} --timerange {range_str} -p {formatted_pairs}"
                print(f"Running command: {cmd}")
                subprocess.run(cmd, shell=True)
        else:
            num_backtest = len(ranges)
            cmd = f"{command} --timerange {range_str}"
            print(f"Running command: {cmd}")
            subprocess.run(cmd, shell=True)

    directory = "user_data/backtest_results/"
    extension = ".json"
    file_list = glob.glob(os.path.join(directory, f"*{extension}"))
    file_list.sort(key=os.path.getmtime, reverse=True)
    filtered_files = [file for file in file_list if "meta" not in os.path.basename(file)]

    latest_files = filtered_files[:num_backtest]
    file_names = [f'freqtrade backtesting-show -c {config_filename} --export-filename="user_data/backtest_results/{os.path.basename(file)}"' for file in latest_files]
    file_names[-1] = file_names[-1].replace(" &&", "")

    end_time = time.time()s

    print(f"\nPrint output: {num_backtest} results\n")
    for name in file_names:
        print(f"Running command: {name}")
        subprocess.run(name, shell=True)

    print(f"\n---> Total time taken: {end_time - start_time}")
else:
    print('Error. Example usage: python3 backtestbcd.py -n 5 -r "freqtrade backtesting --strategy-list teststra -c config_test.json --cache none --export signals --timeframe 1m --max-open-trades 1 --enable-protections" --timerange "20230310-20230311 20230201-20230202 20220610-20220611 20230102-20230104 20230104-"')
