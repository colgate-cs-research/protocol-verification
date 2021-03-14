## Testing random configs

BGP configurations are tested by running create_expect.py on configuration files (in /configs), which creates expect script to systematically add/remove commands from the config. Logs of expect script are stored under /logs. Generated configurated stored under /generated_configs. 

Run `start_tests.sh` to start tests.

bgp_configs_list - contains list of bgp configs from /tests/topotests in the FRR directory.
Those configs were downloaded and put in /configs, using `wget -i bgp_configs_list`

takes about 3.45 minutes to run 6 configs

### Notes
1. Update configs to templates?
2. Other configurations?
3. Try to speed up by having less routers?