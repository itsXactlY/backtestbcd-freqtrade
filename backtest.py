import argparse
import glob
import json
import os
import platform
import subprocess
from calendar import monthrange
from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count
import math
import signal
import sys


start_time = datetime.now()
processes = []


def signal_handler(signal, frame):
    # Terminate all running processes
    for process in processes:
        process.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# Parse command line arguments
parser = argparse.ArgumentParser(description='Support backtest num_pair/total_pair once, different timeranges and output!')
parser.add_argument('-n', '--num_pairs', type=int, default='-1', help='Number of pairs in each command')
parser.add_argument('-r', '--command', type=str, default='freqtrade backtesting --strategy aio -c config_test.json --cache none --export signals --timeframe 5m', help='Ask the highly trained Apes...')
parser.add_argument('-timerange', '--timerange', type=str, default="20210101-20230101", help=' Define Timerange, example: --timerange 20230101-20230201')

args = parser.parse_args()


def split_into_chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def get_config_filename(timerange_start, timerange_end):
    year = timerange_end.year
    month = timerange_end.month

    # Calculate the month before
    if month == 1:
        month_before = 12
        year -= 1
    else:
        month_before = month - 1

    _, num_days = monthrange(year, month_before)
    month_before_date = datetime(year, month_before, num_days)

    formatted_date = month_before_date.strftime("%Y%m%d")

    if platform.system() == "Windows":
        filename = f"user_data\\pairlists\\binance_spot\\USDT\\daily\\daily_200_USDT_0,01_minprice_{formatted_date}.json"
    else:
        filename = f"user_data/pairlists/binance_spot/USDT/daily/daily_200_USDT_0,01_minprice_{formatted_date}.json"

    try:
        with open(filename) as f:
            return filename
    except FileNotFoundError:
        print(f"Warning: File '{filename}' not found. Using pairlist config from previous month instead.")
        return get_config_filename(timerange_start, month_before_date)


# Function to run a backtest command
def run_backtest(args):
    command, month_start_str, month_end_str, formatted_pairs, config_filename = args
    cmd = f"{command} --timerange {month_start_str}-{month_end_str} -p {formatted_pairs} -c {config_filename}"
    print(f"Running command: {cmd}")
    subprocess.Popen(cmd, shell=True)


if __name__ == '__main__':
    try:
        if args.command is not None:
            command = args.command
            timerange = args.timerange

            # Split the command string and timerange string into parts
            parts = command.split()
            ranges = timerange.split("-")

            timerange_start = datetime.strptime(ranges[0], "%Y%m%d")
            timerange_end = datetime.strptime(ranges[1], "%Y%m%d")
            num_months = (timerange_end.year - timerange_start.year) * 12 + (timerange_end.month - timerange_start.month) + 1

            for i in range(num_months):
                month_start = timerange_start + timedelta(days=i * 30)
                month_end = month_start + timedelta(days=30)
                month_start_str = month_start.strftime("%Y%m%d")
                month_end_str = month_end.strftime("%Y%m%d")

                config_filename = get_config_filename(month_start, month_end)
                print(f'\n\n\n\n\n\nUSING {config_filename} \n\n\n\n\n\n')
                with open(config_filename) as f:
                    filtered_lines = [line for line in f if not line.strip().startswith("//")]
                    filtered_content = ''.join(filtered_lines)
                    data = json.loads(filtered_content)

                pair_whitelist = data['exchange']['pair_whitelist']
                if args.num_pairs is not None and args.num_pairs > 0:
                    num_pair_one = args.num_pairs
                    pair_test = list(split_into_chunks(pair_whitelist, num_pair_one))
                    num_backtest = len(pair_test) * num_months
                    print(f"--> OK! Let's run {num_backtest} backtests, please wait....")

                    pool = Pool(math.ceil(cpu_count() -2 / 2))  # Run one process per two CPU cores
                    backtest_args = []
                    for pairs in pair_test:
                        formatted_pairs = ' '.join(pairs)
                        backtest_args.append((command, month_start_str, month_end_str, formatted_pairs, config_filename))

                    pool.map_async(run_backtest, backtest_args)
                    pool.close()
                    pool.join()

                else:
                    num_backtest = num_months
                    formatted_pairs = ' '.join(pair_whitelist)
                    cmd = f"{command} --timerange {month_start_str}-{month_end_str} -p {formatted_pairs} -c {config_filename}"
                    print(f"Running command: {cmd}")
                    subprocess.Popen(cmd, shell=True)

            directory = "user_data/backtest_results/"
            extension = ".json"
            file_list = glob.glob(os.path.join(directory, f"*{extension}"))
            file_list.sort(key=os.path.getmtime, reverse=True)
            filtered_files = [file for file in file_list if "meta" not in os.path.basename(file)]

            latest_files = filtered_files[:num_backtest]
            file_names = [f'freqtrade backtesting-show -c {config_filename} --export-filename="user_data/backtest_results/{os.path.basename(file)}"' for file in latest_files]
            file_names[-1] = file_names[-1].replace(" &&", "")

            # Open the output file for writing
            with open(f"backtest_output_{start_time.strftime('%Y-%m-%d_%H-%M').replace(':', '_')}.txt", "w") as f:
                f.write(f"\nPrint output: {num_backtest} results\n")
                for name in file_names:
                    f.write(f"Running command: {name}\n")
                    # Redirect the output of the command to the file
                    subprocess.run(name, shell=True, stdout=f, stderr=f)

            end_time = datetime.now()

            elapsed_time = end_time - start_time
            total_seconds = int(elapsed_time.total_seconds())
            total_minutes = int(total_seconds // 60)
            total_seconds = int(total_seconds % 60)

            print(f"\n-> Total time taken: {total_minutes} minutes and {total_seconds} seconds ({total_seconds:.2f} seconds)")

        else:
            print('Error. Example usage: python3 backtest.py -n 300 -r "freqtrade backtesting --strategy aio -c config_test.json --cache none --export signals --timeframe 5m" --timerange 20210101-20230101"')

    except Exception as e:
        print(f"Error: {e}")
