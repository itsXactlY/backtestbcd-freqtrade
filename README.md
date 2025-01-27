# Backtesting Script
This script is used to perform backtesting tasks on a set of pairs for a specific time range using the Freqtrade trading bot. The script takes in a configuration file containing a list of pairs to backtest, splits the pairs into chunks, and runs a backtest command for each chunk of pairs. The output of the backtest commands is then saved to a text file.

# Requirements
Python 3.6 or higher

Freqtrade trading bot

Command line interface (CLI)

Pairlist from -> https://github.com/hippocritical/pairlist_generator/ extracted into /freqtrade/user_data/

# Installation
Clone or download the repository into your Freqtrade installation.

Install the Freqtrade trading bot according to the instructions.

# Usage
To use the script, run the following command:

python3 backtest.py -n <num_pairs> -r "<command>" --timerange "<timerange>"

where:

<num_pairs>: the number of pairs to include in each backtest command.

<command>: the backtest command to run. This should be in the format used by Freqtrade, with the relevant parameters for your backtesting strategy.

<timerange>: the time range to backtest. This should be in the format YYYYMMDD-YYYYMMDD, with multiple time ranges separated by spaces.

For example:

- python3 backtest.py -n 10 -r "freqtrade backtesting --strategy my_strategy -c your-config.json --cache none --export signals --timeframe 5m --timerange 20210425-20210610

This will run backtests for the first/best 10 pairs specified in the pairlist/exchange/spot/collateral/file from the month before we start backtesting, with (MAX_PARALLEL_RUNS = xx), using the my_strategy strategy and a 5-minute timeframe. The output of the backtests will be saved to a file called backtest_output-YYYYMMDD-[...].txt

# Notes

- Big shoutout to batcandoi27 for his basecode.

