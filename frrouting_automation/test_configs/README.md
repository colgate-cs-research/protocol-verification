#Testing random configs

BGP configurations are tested by running create_expect.py on configuration files (in /configs), which creates expect script to systematically add/remove commands from the config. Logs of expect script are stored under /logs. 

TODO: Automate process of testing configurations. 
Edit frr_config.py to take configuration as command line arg. 

Have shell script to:
1. Iterate through each config in /configs
2. Run frr_config.py to start with new config (make sure to have catch clause in case of error with config). 
3. Get docker container id. 
4. Copy python script to generate expect file. 
5. Enter docker container, install expect, run `vtysh` and `write file` to write config to file.
6. Run python script to generate expect script, run expect script. 
7. Exit docker container, copy written config and error log to local. 
8. Loop over. 
