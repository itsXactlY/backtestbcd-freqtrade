import json 
import argparse
import subprocess
import time
from datetime import datetime, timedelta

def split_into_chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def get_config_filename(timerange_start):
    month_before = timerange_start - timedelta(days=30)
    formatted_date = month_before.strftime("%Y%m%d")
    return f"user_data\\pairlists\\binance_spot\\USDT\\daily\\daily_200_USDT_0,01_minprice_{formatted_date}.json" 

# Parse command line arguments
parser = argparse.ArgumentParser(description='Support backtest num_pair/total_pair once, different timeranges and output !')
parser.add_argument('-n', '--num_pairs', type=int, default=-1, help='Number of pairs in each command')
parser.add_argument('-r', '--command', type=str, default='python3 backtestbcd.py -n 10 -r "freqtrade backtesting --strategy-list your_stra -c config_test.json --cache none --export signals --timeframe 1m"', help='Send the highly trained Apes...')
# todo :: bugfix the parser args
parser.add_argument('--timerange', '--timerange', type=str, default="20210509-20210524 20210127-20210221 20210518-20210610 20210425-20210610", help=' Define Timerange(s), example: --tr 20230101-20230201 Default: Downtrend -> Uptrend -> Side -> All combined')

args = parser.parse_args()

start_time = datetime.now()

try:
    if args.command is not None:
        command = args.command
        timerange = args.timerange

        # Split the command string 
        parts = command.split()
        
        # Split the timerange string on spaces
        timerange_parts = timerange.split()

        for range_part in timerange_parts:
            if len(range_part) == 8:  # Check if it's a date
                timerange_start = datetime.strptime(range_part, "%Y%m%d")
                timerange_end = timerange_start
            else:
                start_end = range_part.split("-")
                timerange_start = datetime.strptime(start_end[0], "%Y%m%d")
                if len(start_end) > 1:
                    timerange_end = datetime.strptime(start_end[1], "%Y%m%d")
                else:
                    timerange_end = timerange_start  
                
            config_filename = get_config_filename(timerange_start)

            with open(config_filename) as f:
                filtered_lines = [line for line in f if not line.strip().startswith("//")]
                filtered_content = ''.join(filtered_lines)
                data = json.loads(filtered_content)

            pair_whitelist = data['exchange']['pair_whitelist']
            if args.num_pairs > 0:
                num_pair_one = args.num_pairs
                pair_test = list(split_into_chunks(pair_whitelist, num_pair_one))
                num_backtest = len(pair_test) * len(timerange_parts)
                print(f"--> OK! Let's run {num_backtest} backtests, please wait....")
                for i, pairs in enumerate(pair_test):
                    formatted_pairs = ' '.join(pairs)
                    cmd = f"{command} --timerange {range_part} -p {formatted_pairs}"
                    print(f"Running command: {cmd}")
                    subprocess.run(cmd, shell=True)
            else:
                num_backtest = len(timerange_parts)
                cmd = f"{command} --timerange {range_part}"
                print(f"Running command: {cmd}")
                subprocess.run(cmd, shell=True)

        end_time = datetime.now()

        elapsed_time = end_time - start_time
        total_seconds = int(elapsed_time.total_seconds())
        total_minutes = int(total_seconds // 60)
        total_seconds = int(total_seconds % 60)

        print(f"\n---> Total time taken: {total_minutes} minutes and {total_seconds} seconds ({total_seconds:.2f} seconds)")
        
    else:
        print('Error. Example usage: python3 backtest.py -n 5 -r "freqtrade backtesting --strategy-list teststra -c config_test.json --cache none --export signals --timeframe 1m --max-open-trades 1 --enable-protections" --timerange "20230310-20230311 20230201-20230202 20220610-20220611 20230102-20230104 20230104-"')

except Exception as e:
    print(f"Error: {e}")
