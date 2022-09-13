# &: 同时运行
# &&: 前面的命令完成后才运行

python -m monitor.monitor_spiders &

python -m schedulers.binance.binance_symbol_list &
python -m spiders.binance.binance_symbol_list &
python -m spiders.binance.binance_symbol_24h &

python -m schedulers.binance.binance_symbol_kline &
python -m spiders.binance.binance_symbol_kline
