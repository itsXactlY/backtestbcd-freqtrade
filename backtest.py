import argparse
import glob
import json
import os
import platform
import subprocess
from calendar import monthrange
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor


MAX_PARALLEL_RUNS = 12
pairlist_cache = {}
start_time = datetime.now()
processes = []


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
            if filename in pairlist_cache:
                return pairlist_cache[filename]
            with open(filename) as f:
                pairlist_cache[filename] = filename
                return filename

    except FileNotFoundError:
        print(f"Warning: File '{filename}' not found. Using pairlist config from previous month instead.")
        return get_config_filename(timerange_start, month_before_date)


def run_backtest(command):
    print(f"Running command: {command}")
    subprocess.run(command, shell=True)


def run_plotting(backtest_result_file, plotting_command):
    print(f"Running plotting command: {plotting_command}")
    
    # Modify the plotting command to resize the plot candles
    resized_plotting_command = plotting_command.replace('--timeframe 1m', '--timeframe 15m')

    # Check if there were trades in the backtesting result
    with open(backtest_result_file) as f:
        result_data = json.load(f)

    if not result_data["Entries"]:
        print("No trades found for this backtesting result. Skipping plotting.")
        return

    # Continue with the plotting using the modified command
    subprocess.run(resized_plotting_command, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Support backtest num_pair/total_pair once, different timeranges and output!')
    parser.add_argument('-n', '--num_pairs', type=int, default=-1, help='Number of pairs in each command')
    parser.add_argument('-r', '--command', type=str, default='freqtrade backtesting --strategy aio -c config_test.json --cache none --export signals --timeframe 5m', help='Ask the highly trained Apes...')
    parser.add_argument('-t', '--timerange', type=str, default="20210101-20230101", help=' Define Timerange, example: --timerange 20230101-20230201')
    parser.add_argument('-p', '--plot', action='store_true', help='Perform plotting of backtesting results')

    args = parser.parse_args()

    if args.command is not None:
        command = args.command
        timerange = args.timerange

        # Split the command string and timerange string into parts
        parts = command.split()
        ranges = timerange.split("-")

        timerange_start = datetime.strptime(ranges[0], "%Y%m%d")
        timerange_end = datetime.strptime(ranges[1], "%Y%m%d")
        num_months = (timerange_end.year - timerange_start.year) * 12 + (timerange_end.month - timerange_start.month) + 1

        commands = []
        for i in range(num_months):
            month_start = timerange_start + timedelta(days=i * 30)
            month_end = month_start + timedelta(days=30)
            month_start_str = month_start.strftime("%Y%m%d")
            month_end_str = month_end.strftime("%Y%m%d")

            config_filename = get_config_filename(month_start, month_end)
            print(f"\nUSING {config_filename} \n")
            with open(config_filename) as f:
                filtered_lines = [line for line in f if not line.strip().startswith("//")]
                filtered_content = ''.join(filtered_lines)
                data = json.loads(filtered_content)

            pair_whitelist = data['exchange']['pair_whitelist']
            if args.num_pairs is not None and args.num_pairs > 0:
                num_pair_one = args.num_pairs
                pair_test = list(split_into_chunks(pair_whitelist, num_pair_one))
                num_backtest = len(pair_test) * num_months
                print(f"--> OK! Let's run {num_backtest} backtests, splitting them into {num_backtest} chunks to run them in parallel, please wait....")

                if args.num_pairs == -1:
                    # Limit the number of backtests to 1
                    pair_test = pair_test[:1]
                    num_backtest = 1

                for pairs in pair_test:
                    formatted_pairs = ' '.join(pairs)
                    cmd = f"{command} --timerange {month_start_str}-{month_end_str} -p {formatted_pairs} -c {config_filename}"
                    commands.append(cmd)

            else:
                num_backtest = 1
                cmd = f"{command} --timerange {month_start_str}-{month_end_str} -c {config_filename}"
                commands.append(cmd)

        # Execute the commands concurrently using the thread pool
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_RUNS) as executor:
            results = executor.map(run_backtest, commands)

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

        # Perform plotting if specified
        if args.plot is not None and "-p" in command:
            plot_command = "freqtrade plot-dataframe --strategy aio2 -c config_test.json --timeframe 1m"

            # Get the list of pairs with trades from the backtest result JSON
            pairs_with_trades = set()
            for file in latest_files:
                with open(file) as f:
                    result_data = json.load(f)
                    for entry in result_data.get("Entries", []):
                        pair = entry.get("pair")
                        if pair:
                            pairs_with_trades.add(pair)

            if len(pairs_with_trades) > 0:
                formatted_pairs_to_plot = ' '.join(pairs_with_trades)
                plot_command = plot_command.replace("-p", f"-p {formatted_pairs_to_plot}")
                print(f"\nPlotting trades for pairs: {formatted_pairs_to_plot}\n")
                subprocess.run(plot_command, shell=True)
            else:
                print("No trades found for any pairs. Skipping plotting.")


        print(f"\n-> Total time taken: {total_minutes} minutes and {total_seconds} seconds ({total_seconds:.2f} seconds)")

    else:
        print('Error. Example usage: python3 backtest.py -n 200 -r "freqtrade backtesting --strategy StrategyClassName -c config_test.json --cache none --export signals --timeframe 5m" --timerange 20210101-20230101"')
